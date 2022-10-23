import argparse
import os
import struct
import subprocess

# variables
enclen = 1024
securelen = 512
distance = 64


def mx(z, y, sum_, s_u_encrypted_pvr_key_parts, p, e):
    """ MX """
    return ((z >> 5 ^ y << 2) + (y >> 3 ^ z << 4)) ^ ((sum_ ^ y) + (s_u_encrypted_pvr_key_parts[(p & 3) ^ e] ^ z))


def long_to_uint(value):
    """ long to uint """
    if value > 4294967295:
        return value & (2 ** 32 - 1)
    else:
        return value


def load_encryption_key(content_protection_key_):
    """ convert encryption key format """
    chunks, chunk_size = len(content_protection_key_), int(len(content_protection_key_) / 4)
    s_u_encrypted_pvr_key_parts = [int(content_protection_key_[i:i + chunk_size], 16) for i in range(0, chunks, chunk_size)]
    s_u_encryption_key = enclen * [0]
    rounds = 6
    sum_ = 0
    z = s_u_encryption_key[enclen - 1]

    while True:
        sum_ = long_to_uint(sum_ + 0x9e3779b9)
        e = long_to_uint((sum_ >> 2) & 3)
        p = 0
        for p in range(0, enclen - 1):
            y = s_u_encryption_key[p + 1]
            s_u_encryption_key[p] = long_to_uint(s_u_encryption_key[p] + mx(z, y, sum_, s_u_encrypted_pvr_key_parts, p, e))
            z = s_u_encryption_key[p]
        p += 1
        y = s_u_encryption_key[0]
        s_u_encryption_key[enclen - 1] = long_to_uint(s_u_encryption_key[enclen - 1] + mx(z, y, sum_, s_u_encrypted_pvr_key_parts, p, e))
        z = s_u_encryption_key[enclen - 1]
        rounds -= 1
        if not rounds:
            break

    return s_u_encryption_key


def decrypt_pvr(pvr_path, out_path, content_protection_key_):
    """ decrypt pvr with encryption key """
    # convert key
    content_protection_key_ = load_encryption_key(content_protection_key_)
    # read pvr
    with open(pvr_path, "rb") as fr:
        head = fr.read(12)
        byte = fr.read(4)

        body = []
        extra = None
        while byte != b"":
            if len(byte) < 4:
                extra = byte
            else:
                body.append(byte)
            byte = fr.read(4)

        # decrypt content
        b = 0
        i = 0
        for i in range(0, min(len(body), securelen)):
            num = struct.unpack("I", body[i])[0]
            body[i] = num ^ content_protection_key_[b]
            b += 1
            if b >= enclen:
                b = 0
        i += 1
        for i in range(i, len(body), distance):
            num = struct.unpack("I", body[i])[0]
            body[i] = num ^ content_protection_key_[b]
            b += 1
            if b >= enclen:
                b = 0

        # dump pvr
        with open(out_path, "wb") as fw:
            head = head[:3] + b"!" + head[3 + 1:]
            fw.write(head)
            for num in body:
                if isinstance(num, int):
                    fw.write(struct.pack('I', num))
                else:
                    fw.write(num)
            if extra is not None:
                fw.write(extra)


def pvr_to_png(pvr_path, png_path, content_protection_key_=None, suppress=False):
    """ convert pvr to png """
    temp_path = pvr_path + ".pvr.ccz"
    if content_protection_key_:
        decrypt_pvr(pvr_path, temp_path, content_protection_key_)
    else:
        temp_path = pvr_path
    cmd = f"TexturePacker {temp_path} --sheet {png_path} --texture-format png --disable-rotation --allow-free-size --no-trim --data dummy.plist --extrude 0"
    if suppress:
        subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        os.system(cmd)
    if content_protection_key_:
        os.remove(temp_path)
    try:
        os.remove("dummy.plist")
    except FileNotFoundError:
        print(f"[!] Failed to decrypt {pvr_path}")
    else:
        print(f"[*] Decrypted {pvr_path} to {png_path}")


def main():
    parser = argparse.ArgumentParser(description="Decrypt pvr.ccz to png with content protection key")

    parser.add_argument('input', help='path to input .pvr.ccz')
    parser.add_argument('output', help='path to output .png')
    parser.add_argument('-k', '--key', help="content protection key")
    parser.add_argument('-s', '--suppress', action='store_true', help="suppress output from TexturePacker")

    args = parser.parse_args()
    content_protection_key = None
    if args.key:
        if len(args.key) != 32:
            print("[!] Key format is incorrect")
            return
        content_protection_key = args.key
    pvr_to_png(args.input, args.output, content_protection_key, args.suppress)


if __name__ == "__main__":
    main()
