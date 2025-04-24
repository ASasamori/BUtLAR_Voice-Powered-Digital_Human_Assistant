#!/usr/bin/env python3
import sys

sys.stderr.write("This is to stderr\n")
with open('/tmp/test_output.txt', 'w') as f:
    f.write("This test ran successfully\n")

print("This is to stdout")