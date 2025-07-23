#ifndef BASE64_H
#define BASE64_H

int base64_decode(const char *b64_input, unsigned char *output);
int base64_encode(const unsigned char *input, int input_length, char *output);

#endif
