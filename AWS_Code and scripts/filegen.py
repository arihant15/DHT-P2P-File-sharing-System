import os
import random

def gen_word(wordLen):
    word = ''
    for i in range(wordLen):
        word += random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    return word

def dataset_1KB():
    #if not os.path.exists("1KB_dataset"):
    #    os.makedirs("1KB_dataset")
    for i in range(1,2):
            filesize = 0
            while filesize < (1000):
                filecreate = open("Peer/Active-Files/1KB_fda"+str(i)+".txt","a")
                word = gen_word(99)
                filecreate.write(word+"\n")
                filecreate.close()
                fileinfo = os.stat("Peer/Active-Files/1KB_fda"+str(i)+".txt")
                filesize = fileinfo.st_size
            filecreate = open("Peer/Active-Files/1KB_fda"+str(i)+".txt","a")
            word = gen_word(24)
            filecreate.write(word)
            filecreate.close()

def dataset_10KB():
    #if not os.path.exists("10KB_dataset"):
    #    os.makedirs("10KB_dataset")
    for i in range(1,2):
            filesize = 0
            while filesize < (10200):
                filecreate = open("Peer/Active-Files/10KB_fda"+str(i)+".txt","a")
                word = gen_word(99)
                filecreate.write(word+"\n")
                filecreate.close()
                fileinfo = os.stat("Peer/Active-Files/10KB_fda"+str(i)+".txt")
                filesize = fileinfo.st_size
            filecreate = open("Peer/Active-Files/10KB_fda"+str(i)+".txt","a")
            word = gen_word(40)
            filecreate.write(word)
            filecreate.close()

def dataset_100KB():
    #if not os.path.exists("100KB_dataset"):
    #    os.makedirs("100KB_dataset")
    for i in range(1,2):        
        filesize = 0
        while filesize < (102400):
            filecreate = open("Peer/Active-Files/100KB_fda"+str(i)+".txt","a")
            word = gen_word(99)
            filecreate.write(word+"\n")
            filecreate.close()
            fileinfo = os.stat("Peer/Active-Files/100KB_fda"+str(i)+".txt")
            filesize = fileinfo.st_size

def dataset_1MB():
    #if not os.path.exists("1MB_dataset"):
    #    os.makedirs("1MB_dataset")
    for i in range(1,2):        
        filesize = 0
        while filesize < (1048500):
            filecreate = open("Peer/Active-Files/1MB_fda"+str(i)+".txt","a")
            word = gen_word(99)
            filecreate.write(word+"\n")
            filecreate.close()
            fileinfo = os.stat("Peer/Active-Files/1MB_fda"+str(i)+".txt")
            filesize = fileinfo.st_size
        filecreate = open("Peer/Active-Files/1MB_fda"+str(i)+".txt","a")
        word = gen_word(76)
        filecreate.write(word)
        filecreate.close()

def dataset_10MB():
    #if not os.path.exists("10MB_dataset"):
    #    os.makedirs("10MB_dataset")
    for i in range(1,2):        
        filesize = 0
        while filesize < (10485700):
            filecreate = open("Peer/Active-Files/10MB_fda"+str(i)+".txt","a")
            word = gen_word(99)
            filecreate.write(word+"\n")
            filecreate.close()
            fileinfo = os.stat("Peer/Active-Files/10MB_fda"+str(i)+".txt")
            filesize = fileinfo.st_size
        filecreate = open("Peer/Active-Files/10MB_fda"+str(i)+".txt","a")
        word = gen_word(60)
        filecreate.write(word)
        filecreate.close()

def dataset_100MB():
    #if not os.path.exists("100MB_dataset"):
    #    os.makedirs("100MB_dataset")
    for i in range(1,2):
        filesize = 0
        while filesize < (104857600):
            filecreate = open("Peer/Active-Files/100MB_fda"+str(i)+".txt","a")
            word = gen_word(99)
            filecreate.write(word+"\n")
            filecreate.close()
            fileinfo = os.stat("Peer/Active-Files/100MB_fda"+str(i)+".txt")
            filesize = fileinfo.st_size

def dataset_1GB():
    #if not os.path.exists("1GB_dataset"):
    #    os.makedirs("1GB_dataset")
    for i in range(1,2):
        filesize = 0
        while filesize < (1073741800):
            filecreate = open("Peer/Active-Files/1GB_fda"+str(i)+".txt","a")
            word = gen_word(99)
            filecreate.write(word+"\n")
            filecreate.close()
            fileinfo = os.stat("Peer/Active-Files/1GB_fda"+str(i)+".txt")
            filesize = fileinfo.st_size
        filecreate = open("Peer/Active-Files/1GB_fda"+str(i)+".txt","a")
        word = gen_word(24)
        filecreate.write(word)
        filecreate.close()

def main():
    print("**********************************")
    print("Creating 1KB Dataset")
    dataset_1KB()
    print("**********************************")
    print("Creating 10KB Dataset")
    dataset_10KB()
    print("**********************************")
    print("Creating 100KB Dataset")
    dataset_100KB()
    print("**********************************")
    print("Creating 1MB Dataset")
    dataset_1MB()
    print("**********************************")
    print("Creating 10MB Dataset")
    dataset_10MB()
    print("**********************************")
    print("Creating 100MB Dataset")
    dataset_100MB()
    print("**********************************")
    print("Creating 1GB Dataset")
    dataset_1GB()
    print("**********************************")

if __name__ == '__main__':
    main()
