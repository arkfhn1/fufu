#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <oqs/oqs.h>
#include <sys/stat.h>

#define MAX_PATH 1024

// Base64 decode
size_t base64_decode(const char *input, uint8_t *output) {
    FILE *pipe = popen("base64 -d", "w");
    if (!pipe) return 0;
    fwrite(input, 1, strlen(input), pipe);
    pclose(pipe);
    return strlen((char *)output);
}

// Baca private key dari .pv.bin
uint8_t* read_private_key(const char *filename, char *alg_name_out, size_t *key_len_out) {
    FILE *fp = fopen(filename, "rb");
    if (!fp) {
        fprintf(stderr, "ERROR_CODE:ERR_READ_KEY:%s\n", filename);
        return NULL;
    }

    char b64_alg[64] = {0};
    char b64_len[64] = {0};
    fread(b64_alg, 1, 16, fp);
    fread(b64_len, 1, 8, fp);

    // Decode alg name
    char decoded_alg[64];
    FILE *alg_pipe = popen("base64 -d", "w");
    FILE *alg_out = fopen("alg.txt", "w+");
    fprintf(alg_out, "%s", b64_alg);
    fclose(alg_out);
    system("base64 -d alg.txt > alg_decoded.txt");
    FILE *alg_decoded = fopen("alg_decoded.txt", "r");
    fgets(decoded_alg, sizeof(decoded_alg), alg_decoded);
    fclose(alg_decoded);
    remove("alg.txt");
    remove("alg_decoded.txt");
    strcpy(alg_name_out, decoded_alg);

    // Decode key length
    char decoded_len[16];
    FILE *len_pipe = popen("base64 -d", "w");
    FILE *len_out = fopen("len.txt", "w+");
    fprintf(len_out, "%s", b64_len);
    fclose(len_out);
    system("base64 -d len.txt > len_decoded.txt");
    FILE *len_decoded = fopen("len_decoded.txt", "r");
    fgets(decoded_len, sizeof(decoded_len), len_decoded);
    fclose(len_decoded);
    remove("len.txt");
    remove("len_decoded.txt");
    size_t key_len = atoi(decoded_len);

    // Read binary private key
    uint8_t *priv = malloc(key_len);
    fread(priv, 1, key_len, fp);
    fclose(fp);

    *key_len_out = key_len;
    return priv;
}

// Tulis fail signature
void write_signature_file(const char *path, const char *alg_name, const uint8_t *sig, size_t sig_len) {
    FILE *fp = fopen(path, "wb");
    if (!fp) {
        fprintf(stderr, "ERROR_CODE:ERR_WRITE_SIG:%s\n", path);
        return;
    }

    // Encode alg_name
    char cmd1[128], cmd2[128];
    snprintf(cmd1, sizeof(cmd1), "echo -n \"%s\" | base64 -w0 > alg_header.b64", alg_name);
    snprintf(cmd2, sizeof(cmd2), "echo -n \"%zu\" | base64 -w0 > len_header.b64", sig_len);
    system(cmd1);
    system(cmd2);

    FILE *f1 = fopen("alg_header.b64", "rb");
    FILE *f2 = fopen("len_header.b64", "rb");
    char buffer[64];
    while (fgets(buffer, sizeof(buffer), f1)) fwrite(buffer, 1, strlen(buffer), fp);
    while (fgets(buffer, sizeof(buffer), f2)) fwrite(buffer, 1, strlen(buffer), fp);
    fclose(f1); fclose(f2);
    remove("alg_header.b64");
    remove("len_header.b64");

    fwrite(sig, 1, sig_len, fp);
    fclose(fp);
}

int ends_with(const char *str, const char *suffix) {
    if (!str || !suffix) return 0;
    size_t len_str = strlen(str);
    size_t len_suf = strlen(suffix);
    if (len_suf > len_str) return 0;
    return strncmp(str + len_str - len_suf, suffix, len_suf) == 0;
}

int main(int argc, char *argv[]) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <algorithm> <private_key_file> <folder_path>\n", argv[0]);
        return 1;
    }

    const char *alg = argv[1];
    const char *key_path = argv[2];
    const char *folder_path = argv[3];

    char alg_name[64];
    size_t priv_len;
    uint8_t *priv = read_private_key(key_path, alg_name, &priv_len);
    if (!priv) return 2;

    if (strcmp(alg, alg_name) != 0) {
        fprintf(stderr, "ERROR_CODE:ERR_ALG_MISMATCH\n");
        free(priv);
        return 3;
    }

    OQS_SIG *sig = OQS_SIG_new(alg);
    if (!sig) {
        fprintf(stderr, "ERROR_CODE:ERR_SIG_INIT\n");
        free(priv);
        return 4;
    }

    DIR *dir = opendir(folder_path);
    if (!dir) {
        fprintf(stderr, "ERROR_CODE:ERR_OPEN_DIR\n");
        OQS_SIG_free(sig);
        free(priv);
        return 5;
    }

    char sig_folder[MAX_PATH];
    snprintf(sig_folder, sizeof(sig_folder), "%s/signatures", folder_path);
    mkdir(sig_folder, 0700);

    struct dirent *entry;
    while ((entry = readdir(dir)) != NULL) {
        if (entry->d_type != DT_REG) continue;
        if (ends_with(entry->d_name, ".sig")) continue;

        char filepath[MAX_PATH];
        snprintf(filepath, sizeof(filepath), "%s/%s", folder_path, entry->d_name);

        FILE *fp = fopen(filepath, "rb");
        if (!fp) continue;

        fseek(fp, 0, SEEK_END);
        size_t len = ftell(fp);
        fseek(fp, 0, SEEK_SET);
        uint8_t *msg = malloc(len);
        fread(msg, 1, len, fp);
        fclose(fp);

        uint8_t *sig_buf = malloc(sig->length_signature);
        size_t sig_actual_len;

        if (OQS_SIG_sign(sig, sig_buf, &sig_actual_len, msg, len, priv) != OQS_SUCCESS) {
            fprintf(stderr, "ERROR_CODE:ERR_SIGN:%s\n", entry->d_name);
            free(msg);
            free(sig_buf);
            continue;
        }

        char sig_path[MAX_PATH];
        snprintf(sig_path, sizeof(sig_path), "%s/%s.sig", sig_folder, entry->d_name);
        write_signature_file(sig_path, alg_name, sig_buf, sig_actual_len);

        printf("[✔] Signed: %s\n", entry->d_name);
        free(msg);
        free(sig_buf);
    }

    closedir(dir);
    OQS_SIG_free(sig);
    free(priv);
    return 0;
}
