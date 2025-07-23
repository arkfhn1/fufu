#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <oqs/oqs.h>
#include <stdint.h>
#include <openssl/bio.h>
#include <openssl/evp.h>

#define HEADER_ALGO_BASE64_LEN 16
#define HEADER_KEYLEN_BASE64_LEN 8
#define HEADER_TOTAL_LEN (HEADER_ALGO_BASE64_LEN + HEADER_KEYLEN_BASE64_LEN)

int base64_decode(const char *b64input, uint8_t *buffer, size_t max_len) {
    BIO *bio, *b64;
    int decoded_len = 0;

    b64 = BIO_new(BIO_f_base64());
    bio = BIO_new_mem_buf((void *)b64input, -1);
    bio = BIO_push(b64, bio);
    BIO_set_flags(bio, BIO_FLAGS_BASE64_NO_NL); // Jangan baca newline

    decoded_len = BIO_read(bio, buffer, max_len);
    BIO_free_all(bio);
    return decoded_len;
}

void write_signature_file(const char *b64_algo, const uint8_t *signature, size_t sig_len, const char *output_path) {
    FILE *f = fopen(output_path, "wb");
    if (!f) {
        fprintf(stderr, "ERR_FILE_WRITE: Gagal buka %s\n", output_path);
        return;
    }

    fwrite(b64_algo, 1, strlen(b64_algo), f); // Tulis base64 algo (16 byte)
    fwrite(signature, 1, sig_len, f);         // Tulis binary signature
    fclose(f);
}

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "USAGE: %s <private_key.bin> <input_file> <output.sig>\n", argv[0]);
        return 1;
    }

    const char *priv_key_path = argv[1];
    const char *input_file = argv[2];
    const char *sig_output_file = argv[3];

    // Baca fail .bin
    FILE *f = fopen(priv_key_path, "rb");
    if (!f) {
        fprintf(stderr, "ERR_PRIV_KEY_READ: Gagal buka %s\n", priv_key_path);
        return 2;
    }

    fseek(f, 0, SEEK_END);
    size_t file_size = ftell(f);
    rewind(f);

    if (file_size <= HEADER_TOTAL_LEN) {
        fprintf(stderr, "ERR_FILE_SIZE: Fail terlalu kecil\n");
        fclose(f);
        return 3;
    }

    uint8_t *buffer = malloc(file_size);
    fread(buffer, 1, file_size, f);
    fclose(f);

    // Decode algoritma base64 (16 byte)
    char b64_algo[HEADER_ALGO_BASE64_LEN + 1] = {0};
    memcpy(b64_algo, buffer, HEADER_ALGO_BASE64_LEN);

    char algo_name[32] = {0};
    int algo_len = base64_decode(b64_algo, (uint8_t *)algo_name, sizeof(algo_name));
    if (algo_len <= 0) {
        fprintf(stderr, "ERR_ALGO_DECODE: Gagal decode algoritma\n");
        free(buffer);
        return 4;
    }
    algo_name[algo_len] = '\0';

    // Decode panjang kunci (8 byte base64)
    char b64_keylen[HEADER_KEYLEN_BASE64_LEN + 1] = {0};
    memcpy(b64_keylen, buffer + HEADER_ALGO_BASE64_LEN, HEADER_KEYLEN_BASE64_LEN);

    char keylen_str[8] = {0};
    int keylen_len = base64_decode(b64_keylen, (uint8_t *)keylen_str, sizeof(keylen_str));
    if (keylen_len <= 0) {
        fprintf(stderr, "ERR_KEYLEN_DECODE: Gagal decode panjang kunci\n");
        free(buffer);
        return 5;
    }
    keylen_str[keylen_len] = '\0';

    int key_len = atoi(keylen_str);
    if (key_len <= 0 || file_size < HEADER_TOTAL_LEN + key_len) {
        fprintf(stderr, "ERR_KEYLEN_INVALID: Panjang kunci tidak sah\n");
        free(buffer);
        return 6;
    }

    uint8_t *priv_key = buffer + HEADER_TOTAL_LEN;

    // Inisialisasi OQS
    OQS_SIG *sig = OQS_SIG_new(algo_name);
    if (!sig) {
        fprintf(stderr, "ERR_ALGO_INIT: Algoritma tidak disokong: %s\n", algo_name);
        free(buffer);
        return 7;
    }

    // Baca fail input
    FILE *f_input = fopen(input_file, "rb");
    if (!f_input) {
        fprintf(stderr, "ERR_INPUT_FILE: Gagal buka %s\n", input_file);
        OQS_SIG_free(sig);
        free(buffer);
        return 8;
    }

    fseek(f_input, 0, SEEK_END);
    size_t msg_len = ftell(f_input);
    rewind(f_input);

    uint8_t *msg = malloc(msg_len);
    fread(msg, 1, msg_len, f_input);
    fclose(f_input);

    // Tandatangan
    uint8_t *sig_buf = malloc(sig->length_signature);
    size_t sig_len = 0;

    if (OQS_SIG_sign(sig, sig_buf, &sig_len, msg, msg_len, priv_key) != OQS_SUCCESS) {
        fprintf(stderr, "ERR_SIGN: Gagal tandatangan mesej\n");
        OQS_SIG_free(sig);
        free(buffer);
        free(msg);
        free(sig_buf);
        return 9;
    }

    write_signature_file(b64_algo, sig_buf, sig_len, sig_output_file);
    fprintf(stderr, "[✔] Tandatangan berjaya → %s\n", sig_output_file);

    OQS_SIG_free(sig);
    free(buffer);
    free(msg);
    free(sig_buf);
    return 0;
}
