import os
import tarfile
import gnupg

class GPGEncrypt():
    
    def __init__(self, path_to_data : str, output_path : str, passwd : str):
        self._passwd = passwd
        self._out = output_path
        # Set GPG Home directory
        self._gpg = gnupg.GPG()
        # Set GPG Encoding
        self._gpg.encoding = 'utf-8'
        # Get dataToEncrypt full path
        self._dataToEncrypt = path_to_data
        # Setup tar filename to end with .zip
        self._tarFile = ("{}.tar".format(self._dataToEncrypt))
        # Setup encrypted filename to end with .gpg
        self._encryptedFile = ("{}.tar.gpg".format(self._dataToEncrypt))
        
    def encrypt(self):
        self._dataTar()
        self._encryptFile()
    
    def _dataTar(self):
        if os.path.isfile(self._dataToEncrypt):
            return
        else:
            with tarfile.open(self._tarFile, 'w|') as tar:
                tar.add(self._dataToEncrypt)
                tar.close()

    def _encryptFile(self):
        passphrase = (self._passwd)
        input = self._gpg.gen_key_input(name_email='user1@test', passphrase=passphrase)
        fp = self._gpg.gen_key(input).fingerprint
        if os.path.isfile(self._dataToEncrypt):
            with open(self._dataToEncrypt, 'rb') as f:
                status = self._gpg.encrypt_file(f,
                fp,
                symmetric='AES256',
                passphrase=passphrase,
                armor=False,
                output=self._out + ".gpg")

        else:
            with open(self._tarFile, 'rb') as f:
                status = self._gpg.encrypt_file(f,
                fp,
                symmetric='AES256',
                passphrase=passphrase,
                armor=False,
                output=self._out + ".tar.gpg")
                
        os.remove(self._tarFile)
        
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

        # Extract the tar archive to the output path
        try:
            with tarfile.open(fileobj=decrypted_data.data, mode='r:gz') as tar:
                tar.extractall(path=self.output_path)
        except tarfile.TarError as e:
            print(f"Error: Failed to extract the tar archive: {e}")
            os._exit(-1)