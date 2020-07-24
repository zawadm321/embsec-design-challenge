from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Util import Padding
from Crypto.Signature import pkcs1_15
import struct
"""
f = unencrypted firmware
F = encrypted firmware
metadata = version | size(f) | size(F)
signed(hash(metadata | IV | F)) | metadata | IV | F
"""
def protect_firmware(infile, outfile, version, message):
    """
    Arguments are:
    {infile} contains the firmware to be protected.
    {outfile} is where the encrypted firmware blob is written.
    {version} is the version of the firmware -- a positive integer value, or 0 to debug the firmware.
    {message} is the release message, which gets appended to the firmware and encrypted with it.
    firmware = firmware + message + "\0"
    
    Takes keys generated by the {bl_build} tool from "secret_build_output.txt". 
    The {aes_key} is used to encrypt the firmware {fw},
    and the {rsa_key} is used to sign the hash of a copy of the metadata, IV, and encrypted firmware.
    
    The plaintext and encrypted firmware will be referred to as "f" and "F" respectively.
    The overall structure of the firmware blob is such:
    
    metadata = version | size(f) | size(F)
    signed(hash(metadata | IV | F)) | metadata | IV | F
    
    Returns: 0
    Outputs: {outfile}
    """
    with open(infile, 'rb') as f: # reads firmware
        fw = f.read()
        
    metadata = struct.pack("<HH", version, len(fw)) # packs initial metadata: version, length  of unencrypted firmware
    fw = fw + message.encode() + b'\00' # appends release message to end of firmware
    
    with open("secret_build_output.txt", 'rb') as sec_output:
        aes_key = sec_output.read(16) # get symmetric key
        rsa_key = RSA.import_key(sec_output.read()) # get private key
        
    cipher = AES.new(aes_key, AES.MODE_CBC) # creates AES object
    
    encrypted_fw = cipher.encrypt(Padding.pad(fw, AES.block_size)) # encrypts firmware
    
    metadata += struct.pack("<H", len(encrypted_fw)) # adds the length of encrypted firmware to metadata
    
    hashed_fw = SHA256.new(data = metadata + cipher.iv + encrypted_Fw) # hashes the metadata, IV, and encrypted firmware
    
    signature = pkcs1_15.new(rsa_key).sign(hashed_fw) # signs the hashed metadata, IV, and firmware using the private key
    
    fw_blob = signature + metadata + cipher.iv + encrypted_fw # creates blob to be sent to bootloader
    
    with open(outfile, "w+b") as out: # writes firmware blob to outfile
        out.write(fw_blob)
    return 0
