#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "utils.h"
#include "base64.h"

// Fungsi membaca header dari fail key atau signature
int read_key_or_sig_header(FILE *fp, char *algo_out, size_t algo_len, int is_keyfile) {
    char buffer[2048];
    size_t bytes_read = fread(buffer, 1, sizeof(buffer), fp);
    if (bytes_read == 0) return 0;

    char *algo_b64 = NULL;
    char *size_b64 = NULL;

    // Cari dua baris yang diakhiri '=='
    int found = 0;
    size_t start = 0;
    for (size_t i = 0; i < bytes_read; ++i) {
        if (buffer[i] == '=' && buffer[i+1] == '=') {
            size_t end = i + 2;
            size_t len = end - start;

            char *line = (char *)malloc(len + 1);
            memcpy(line, buffer + start, len);
            line[len] = '\0';

            if (found == 0) algo_b64 = line;
            else if (found == 1) size_b64 = line;

            found++;
            i += 1;
            start = i + 1;

            if ((!is_keyfile && found == 1) || (is_keyfile && found == 2))
                break;
        }
    }

    if (!algo_b64) return 0;

    // Decode algorithm
    unsigned char algo_dec[128] = {0};
    int algo_len_dec = base64_decode(algo_b64, algo_dec);
    if (algo_len_dec <= 0) {
        free(algo_b64);
        if (size_b64) free(size_b64);
        return 0;
    }

    strncpy(algo_out, (char *)algo_dec, algo_len - 1);
    algo_out[algo_len - 1] = '\0';

    free(algo_b64);
    if (size_b64) free(size_b64);

    // Reset file pointer ke lepas header
    fseek(fp, start, SEEK_SET);
    return 1;
}
