#!/usr/bin/env python3

import time

VERSION = "2.0.0"

def main():
    while True:
        print("============================")
        print(f"  OTA Sample App v{VERSION}")
        print("============================")
        print("Hello from Raspberry Pi!")
        print(f"Running version: {VERSION}")
        print("")
        time.sleep(5)  # prints every 5 seconds

if __name__ == "__main__":
    main()
