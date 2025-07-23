#ifndef UTILS_H
#define UTILS_H

int read_key_or_sig_header(FILE *fp, char *algo_out, size_t algo_len, int is_keyfile);

#endif
