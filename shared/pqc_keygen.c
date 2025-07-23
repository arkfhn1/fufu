#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <oqs/oqs.h>
#include <stdint.h>
#include <time.h>

void write_key_file(const char *filename, const char *alg_name, const uint8_t *key, size_t key_len) {
    FILE *fp = fopen(filename, "wb");
    if (!fp) {
        fprintf(stderr, "ERROR_CODE:ERR_FILE_WRITE:%s\n", filename);
        exit(2);
    }

    // Base64 encode alg_name (tanpa newline)
    char base64_alg[256] = {0};
    snprintf(base64_alg, sizeof(base64_alg), "echo -n \"%s\" | base64 -w0", alg_name);
    FILE *alg_pipe = popen(base64_alg, "r");
    if (alg_pipe) {
        char buffer[256];
        if (fgets(buffer, sizeof(buffer), alg_pipe)) {
            fwrite(buffer, 1, strlen(buffer), fp);
        }
        pclose(alg_pipe);
    }

    // Base64 encode key_len (tanpa newline)
    char len_str[32];
    snprintf(len_str, sizeof(len_str), "%zu", key_len);
    char base64_len[64] = {0};
    snprintf(base64_len, sizeof(base64_len), "echo -n \"%s\" | base64 -w0", len_str);
    FILE *len_pipe = popen(base64_len, "r");
    if (len_pipe) {
        char buffer[64];
        if (fgets(buffer, sizeof(buffer), len_pipe)) {
            fwrite(buffer, 1, strlen(buffer), fp);
        }
        pclose(len_pipe);
    }

    // Terus tulis binary key data (sambung terus)
    fwrite(key, 1, key_len, fp);
    fclose(fp);
}

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <algorithm> <output_pb_file> <output_pv_file>\n", argv[0]);
        return 1;
    }

    const char *alg_name = argv[1];
    const char *pb_file = argv[2];
    const char *pv_file = argv[3];

    OQS_SIG *sig = NULL;
    uint8_t *public_key = NULL;
    uint8_t *private_key = NULL;

    if (!OQS_SIG_alg_is_enabled(alg_name)) {
        fprintf(stderr, "ERROR_CODE:ERR_ALGO_UNSUPPORTED:%s\n", alg_name);
        return 2;
    }

    sig = OQS_SIG_new(alg_name);
    if (sig == NULL) {
        fprintf(stderr, "ERROR_CODE:ERR_SIG_INIT_FAILED\n");
        return 3;
    }

    public_key = malloc(sig->length_public_key);
    private_key = malloc(sig->length_secret_key);
    if (!public_key || !private_key) {
        fprintf(stderr, "ERROR_CODE:ERR_MEMORY_ALLOC\n");
        OQS_SIG_free(sig);
        return 4;
    }

    if (OQS_SIG_keypair(sig, public_key, private_key) != OQS_SUCCESS) {
        fprintf(stderr, "ERROR_CODE:ERR_KEYGEN_FAILED\n");
        OQS_SIG_free(sig);
        return 5;
    }

    write_key_file(pb_file, alg_name, public_key, sig->length_public_key);
    write_key_file(pv_file, alg_name, private_key, sig->length_secret_key);

    printf("Key pair generated successfully for algorithm: %s\n", alg_name);

    OQS_MEM_secure_free(public_key, sig->length_public_key);
    OQS_MEM_secure_free(private_key, sig->length_secret_key);
    OQS_SIG_free(sig);
    return 0;
}
