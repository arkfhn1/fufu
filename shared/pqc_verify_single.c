#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <oqs/oqs.h>
#include "utils.h"
#include "base64.h"

int main(int argc, char *argv[]) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <public_key.bin> <input_file> <signature.sig>\n", argv[0]);
        return 1;
    }

    const char *pubkey_path = argv[1];
    const char *input_path = argv[2];
    const char *sig_path = argv[3];

    // Buka fail public key
    FILE *fp_pub = fopen(pubkey_path, "rb");
    if (!fp_pub) {
        fprintf(stderr, "ERR_READ_FILE: Tidak dapat buka fail %s\n", pubkey_path);
        return 1;
    }

    char algo_key[128];
    if (!read_key_or_sig_header(fp_pub, algo_key, sizeof(algo_key), 1)) {
        fprintf(stderr, "ERR_HEADER_INVALID: Header tidak sah dalam %s\n", pubkey_path);
        fclose(fp_pub);
        return 1;
    }

    // Inisialisasi OQS_SIG
    OQS_SIG *sig = OQS_SIG_new(algo_key);
    if (sig == NULL) {
        fprintf(stderr, "ERR_ALGO_INIT: Algoritma tidak disokong: %s\n", algo_key);
        fclose(fp_pub);
        return 1;
    }

    // Baca public key
    uint8_t *public_key = malloc(sig->length_public_key);
    if (fread(public_key, 1, sig->length_public_key, fp_pub) != sig->length_public_key) {
        fprintf(stderr, "ERR_KEY_READ: Gagal baca public key\n");
        fclose(fp_pub);
        OQS_SIG_free(sig);
        free(public_key);
        return 1;
    }
    fclose(fp_pub);

    // Buka dan baca signature
    FILE *fp_sig = fopen(sig_path, "rb");
    if (!fp_sig) {
        fprintf(stderr, "ERR_READ_FILE: Tidak dapat buka fail %s\n", sig_path);
        OQS_SIG_free(sig);
        free(public_key);
        return 1;
    }

    char algo_sig[128];
    if (!read_key_or_sig_header(fp_sig, algo_sig, sizeof(algo_sig), 0)) {
        fprintf(stderr, "ERR_HEADER_INVALID: Header tidak sah dalam %s\n", sig_path);
        fclose(fp_sig);
        OQS_SIG_free(sig);
        free(public_key);
        return 1;
    }

    if (strcmp(algo_key, algo_sig) != 0) {
        fprintf(stderr, "ERR_ALGO_MISMATCH: Algoritma %s != %s\n", algo_key, algo_sig);
        fclose(fp_sig);
        OQS_SIG_free(sig);
        free(public_key);
        return 1;
    }

    // Baca signature selepas header
    uint8_t *signature = malloc(sig->length_signature);
    if (fread(signature, 1, sig->length_signature, fp_sig) != sig->length_signature) {
        fprintf(stderr, "ERR_SIG_READ: Gagal baca signature\n");
        fclose(fp_sig);
        OQS_SIG_free(sig);
        free(public_key);
        free(signature);
        return 1;
    }
    fclose(fp_sig);

    // Baca kandungan input file
    FILE *fp_input = fopen(input_path, "rb");
    if (!fp_input) {
        fprintf(stderr, "ERR_READ_FILE: Tidak dapat buka fail %s\n", input_path);
        OQS_SIG_free(sig);
        free(public_key);
        free(signature);
        return 1;
    }

    fseek(fp_input, 0, SEEK_END);
    size_t input_len = ftell(fp_input);
    rewind(fp_input);

    uint8_t *input_msg = malloc(input_len);
    fread(input_msg, 1, input_len, fp_input);
    fclose(fp_input);

    // Verifikasi
    OQS_STATUS status = OQS_SIG_verify(sig, input_msg, input_len, signature, sig->length_signature, public_key);
    if (status != OQS_SUCCESS) {
        fprintf(stderr, "ERR_VERIFY_FAILED: Tandatangan tidak sah\n");
    } else {
        printf("[✔] Tandatangan sah: %s\n", input_path);
    }

    // Cleanup
    OQS_SIG_free(sig);
    free(public_key);
    free(signature);
    free(input_msg);
    return status != OQS_SUCCESS;
}
