import hashlib
import os

import boto3
from cryptography.fernet import Fernet

print(f"Saving to: {os.getcwd()}")


def save_key(key, key_path='backup.key'):
    with open(key_path, 'wb') as f:
        f.write(key)
    print(f"✓ Key saved: {key_path}")


def load_key(key_path='backup.key'):
    with open(key_path, 'rb') as f:
        return f.read()


KEY = Fernet.generate_key()
save_key(KEY)
fernet = Fernet(KEY)


def encrypt_file(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
        encrypted = fernet.encrypt(data)
    print(f"✓ Encrypted {file_path}")
    return encrypted


def save_encrypted(file_path, encrypted_data):
    encrypted_path = file_path + '.enc'
    with open(encrypted_path, 'wb') as f:
        f.write(encrypted_data)
    print(f"✓ Saved encrypted file: {encrypted_path}")
    return encrypted_path


def backup_to_s3(encrypted_path, bucket_name):
    session = boto3.Session(profile_name='cloud-plus-s3-pipeline')
    s3 = session.client('s3')
    s3.upload_file(
        encrypted_path, bucket_name, os.path.basename(encrypted_path)
    )
    print(f"✓ Uploaded {encrypted_path} to {bucket_name}")


def generate_checksum(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    checksum = sha256.hexdigest()
    print(f"✓ Checksum for {file_path}: {checksum}")
    return checksum


def verify_integrity(checksum_a, checksum_b):
    if checksum_a == checksum_b:
        print("✓ Integrity verified — checksums match")
    else:
        print("✗ Integrity check FAILED — checksums differ")


def restore_from_s3(bucket_name, encrypted_filename):
    session = boto3.Session(profile_name='cloud-plus-s3-pipeline')
    s3 = session.client('s3')
    s3.download_file(bucket_name, encrypted_filename, encrypted_filename)

    downloaded_checksum = generate_checksum(encrypted_filename)

    with open(encrypted_filename, 'rb') as f:
        encrypted_data = f.read()
    decrypted_data = fernet.decrypt(encrypted_data)
    restored_filename = encrypted_filename.replace('.enc', '.restored')
    with open(restored_filename, 'wb') as f:
        f.write(decrypted_data)
    print(f"✓ Restored file: {restored_filename}")

    return downloaded_checksum


# --- main flow ---
encrypted = encrypt_file('test.txt')
encrypted_path = save_encrypted('test.txt', encrypted)
checksum = generate_checksum(encrypted_path)
backup_to_s3(encrypted_path, 'cloud-plus-blake-lab')
downloaded_checksum = restore_from_s3('cloud-plus-blake-lab', 'test.txt.enc')
verify_integrity(checksum, downloaded_checksum)
