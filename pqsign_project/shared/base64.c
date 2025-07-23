#include <stdlib.h>
#include <string.h>
#include <openssl/bio.h>
#include <openssl/evp.h>
#include <openssl/buffer.h>  // ✅ Tambah ini
#include "base64.h"

int base64_decode(const char *b64_input, unsigned char *output) {
    BIO *bio, *b64;
    int decodeLen = strlen(b64_input);
    int len = 0;

    bio = BIO_new_mem_buf(b64_input, -1);
    b64 = BIO_new(BIO_f_base64());
    BIO_set_flags(b64, BIO_FLAGS_BASE64_NO_NL); // Tanpa newline
    bio = BIO_push(b64, bio);
    len = BIO_read(bio, output, decodeLen);
    BIO_free_all(bio);

    return len;
}

int base64_encode(const unsigned char *input, int input_length, char *output) {
    BIO *b64, *bio;
    BUF_MEM *bufferPtr;

    b64 = BIO_new(BIO_f_base64());
    BIO_set_flags(b64, BIO_FLAGS_BASE64_NO_NL); // Tanpa newline
    bio = BIO_new(BIO_s_mem());
    b64 = BIO_push(b64, bio);

    BIO_write(b64, input, input_length);
    BIO_flush(b64);
    BIO_get_mem_ptr(b64, &bufferPtr);

    memcpy(output, bufferPtr->data, bufferPtr->length);
    output[bufferPtr->length] = '\0';

    BIO_free_all(b64);
    return bufferPtr->length;
}
