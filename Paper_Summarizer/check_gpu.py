import torch
import subprocess

def get_gpu_info():
    print("PyTorch version:", torch.__version__)
    print("CUDA available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("CUDA version:", torch.version.cuda)
        print("GPU device:", torch.cuda.get_device_name(0))
        
        # Get NVIDIA driver version
        try:
            nvidia_smi = subprocess.check_output("nvidia-smi", shell=True)
            print("\nNVIDIA-SMI output:")
            print(nvidia_smi.decode())
        except:
            print("Could not run nvidia-smi")

if __name__ == "__main__":
    get_gpu_info() 