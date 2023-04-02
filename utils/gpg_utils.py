import os
import tarfile
import gnupg
import shutil
from pathlib import Path

class GPGEncrypt():
    
    def __init__(self, input_path, output_path, password):
        self.input_path = input_path
        self.password = password
        self.output_path = output_path
        self.gpg = gnupg.GPG()
        
    def encrypt(self):
        # Compress the input path to a tar file
        if os.path.isfile(self.input_path):
            base_name = os.path.basename(self.input_path)
            dir_name = os.path.dirname(self.input_path)
            tar_path = shutil.make_archive(base_name, 'tar', dir_name, base_name)
        elif os.path.isdir(self.input_path):
            tar_path = shutil.make_archive('archive', 'tar', self.input_path)
        else:
            raise ValueError('Input path is not a file or directory')
        
        # Encrypt the tar file with GPG
        Path(self.output_path).mkdir(parents=True, exist_ok=True)
        with open(tar_path, 'rb') as f:
            encrypted_data = self.gpg.encrypt_file(
                f,
                recipients=None,
                symmetric='AES256',
                passphrase=self.password,
                output=os.path.join(self.output_path, os.path.basename(tar_path) + '.gpg')
            )
        
        # Delete the tar file
        os.remove(tar_path)
        
        return encrypted_data
        
class GPGDecryptAndExtract:
    
    def __init__(self, input_path, password, output_path):
        self.input_path = input_path
        self.password = password
        self.output_path = output_path
        
    def decrypt_and_extract(self):
        # Initialize GPG object
        gpg = gnupg.GPG()
        
        # Decrypt the file
        with open(self.input_path, 'rb') as f:
            decrypted_data = gpg.decrypt_file(f, passphrase=self.password)
            if not decrypted_data.ok:
                print("Error: Decryption failed.")
                os._exit(-1)
                
        with open("temp.tar", "wb") as f:
            f.write(decrypted_data.data)

        # Extract the tar archive to the output path
        try:
            with tarfile.open("temp.tar") as tar:
                tar.extractall(path=self.output_path)
        except tarfile.TarError as e:
            print(f"Error: Failed to extract the tar archive: {e}")
            os._exit(-1)
            
        os.remove("temp.tar")