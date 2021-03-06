import cv2
import numpy as np
import random
import glob
import matplotlib.pyplot as plt

global key
global keyfile


def readCamera():
    '''
    A real-time face detection method
    :return: None
    '''
    cv2.namedWindow('Detecting')
    video = cv2.VideoCapture(0)
    ret, frame = video.read()
    classifier = cv2.CascadeClassifier("haarcascade_frontalface_alt.xml")

    while(ret):
        ret, frame = video.read()
        size = frame.shape[:2]

        img = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

        height,width = size
        minSize = (width/10,height/10)


        faces = classifier.detectMultiScale(img,1.2,2,cv2.CASCADE_SCALE_IMAGE,minSize)
        if len(faces)>0:
            for face in faces:
                x,y,width,height = face
                cv2.rectangle(frame,(x,y),(x+width,y+height),color=(0,255,0))
                screenshot = frame[y:y+height,x:x+width]
                screenshot = cv2.resize(screenshot,(64,64))
                screenshot = cv2.cvtColor(screenshot,cv2.COLOR_BGR2GRAY)
                key = cv2.waitKey(100)
                if key == ord('s'):
                    cv2.imwrite("Keyface.pgm",screenshot)
        cv2.imshow('test',frame)
        key2 = cv2.waitKey(100)
        if key2 == ord('q'):
            break
    cv2.destroyAllWindows()


def LoadImage(path):
    '''
    Load image from a database
    :param path: database location
    :return: a set of faces
    '''
    # make an empty numpy matrix for 1000 sample images
    Faceset = np.mat(np.zeros((15,64*64)))
    i = 0
    # use glob library to get access to each image
    for file in glob.glob(path):
            img = cv2.imread(file,0)

            # strech the matrix to a one-dimensional array
            Faceset[i,:] = np.mat(img).flatten()
            i+=1
    return Faceset


def EigenVector(threshold):
    '''
    Eigenface computation
    :param threshold: threshold
    :return:average image, covariance vectors, difference matrix
    '''
    path = "/Users/HandsomeVincent/Documents/Facedatabase/*.pgm"
    # transpose the faceset
    Faceset = LoadImage(path).T
    # compute average image
    avgImg = np.mean(Faceset,1)
    avgFace = np.reshape(avgImg,(64,64))
    print "The shape of face set is " + str(Faceset.shape)
    print "------------------------------------------------------------"
    print "The shape of average face is " + str(avgFace.shape)
    # obtain difference matrix by subtracting average image from faceset
    differenceMatrix = Faceset - avgImg
    # use built-in function to obtain eigenvalue and eigenvectors
    eigenValues, eigenVectors = np.linalg.eig(np.mat(differenceMatrix.T*differenceMatrix))
    # sort the eigenvalues
    eigenIndex = np.argsort(-eigenValues)
    # keep useful features
    for i in range(Faceset.shape[1]):
        if (eigenValues[eigenIndex[:i]] / eigenValues.sum()).sum() >= threshold:
            eigenIndex = eigenIndex[:i]
            break
    # compute covariance vectors
    covarianceVectors = differenceMatrix * eigenVectors[:,eigenIndex]
    plt.imshow(avgFace,'Greys')
    plt.show()
    print "------------------------------------------------------------"
    print "The shape of main features' covariance vectors is " + str(covarianceVectors.shape)
    print "------------------------------------------------------------"
    return avgImg,covarianceVectors,differenceMatrix

def Recognize(inputImg,Facevector,avgImg,difference):
    # computer difference
    diff = inputImg.T - avgImg
    weightedVec = Facevector.T * diff
    threshold = 1.5 * (10 ** 13)
    for i in range(15):
        TrainVec = Facevector.T * difference[:,i]
        # if the input image's Euclidean distance is close enough, recognized
        if (np.array(weightedVec-TrainVec)**2).sum() < threshold:
            print "No." + str(i+1) + " image in this folder is matched ! "
            return True
    return False

def encrypt(img):
    '''
    Encrypt the image by randomly switching blocks
    :param img: the image to be encrypted
    :return: Encrypted image, keylist 1 and keylist 2
    '''
    numofblock = 100
    blocknum = int(np.sqrt(numofblock))
    originallist = []
    blankimg = np.zeros(img.shape,dtype=np.uint8)


    blockwidth = img.shape[1] / blocknum
    blockheight = img.shape[0] / blocknum
    blankblock = np.zeros((blockheight,blockwidth,3),dtype=np.uint8)
    blockwidth2 = blockwidth / blocknum
    blockheight2 = blockheight / blocknum
    for i in range(numofblock):
        originallist.append(i)
    keylist1 = random.sample(originallist,numofblock)
    keylist2 = random.sample(originallist,numofblock)
    for i in range(numofblock):
        # print i
        row = i / blocknum + 1
        column = i % blocknum + 1
        rowofblock = keylist1[i] / blocknum + 1
        columnofblock = keylist1[i] % blocknum + 1
        block = img[(rowofblock-1) * blockheight: rowofblock * blockheight, (columnofblock - 1) * blockwidth: columnofblock * blockwidth]
        for j in range(numofblock):
            row2 = j / blocknum + 1
            column2 = j % blocknum + 1
            rowofblock2 = keylist2[j] / blocknum + 1
            columnofblock2 = keylist2[j] % blocknum + 1
            block2 = block[(rowofblock2-1) * blockheight2: rowofblock2 * blockheight2, (columnofblock2 - 1) * blockwidth2: columnofblock2 * blockwidth2]
            blankblock[(row2-1)*blockheight2:row2*blockheight2,(column2-1)*blockwidth2:column2*blockwidth2] = block2

        blankimg[(row-1)*blockheight:row*blockheight,(column-1)*blockwidth:column*blockwidth] = blankblock
    return blankimg,keylist1,keylist2


def decrypt(img,keylist1,keylist2):
    '''
    Decrypt the image
    :param img: image to be decrypted
    :param keylist1: keylist for big blocks
    :param keylist2: keylist for small blocks
    :return: original image
    '''
    blankimg = np.zeros(img.shape,dtype=np.uint8)
    numofblock = 100
    blocknum = int(np.sqrt(numofblock))

    blockheight = img.shape[0] / blocknum
    blockwidth = img.shape[1] / blocknum
    blockheight2 = blockheight / blocknum
    blockwidth2 = blockwidth / blocknum
    blankblock = np.zeros((blockheight,blockwidth,3),dtype=np.uint8)

    for i in range(numofblock):
        rowofblock = i / blocknum + 1
        columnofblock = i % blocknum + 1
        row = keylist1[i] / blocknum + 1
        column = keylist1[i] % blocknum + 1
        block = img[(rowofblock-1) * blockheight: rowofblock * blockheight, (columnofblock - 1) * blockwidth: columnofblock * blockwidth]

        for j in range(numofblock):
            rowofblock2 = j / blocknum + 1
            columnofblock2 = j % blocknum + 1
            row2 = keylist2[j] / blocknum + 1
            column2 = keylist2[j] % blocknum + 1
            block2 = block[(rowofblock2-1) * blockheight2: rowofblock2 * blockheight2, (columnofblock2 - 1) * blockwidth2: columnofblock2 * blockwidth2]
            blankblock[(row2-1)*blockheight2:row2*blockheight2,(column2-1)*blockwidth2:column2*blockwidth2] = block2
        blankimg[(row-1)*blockheight:row*blockheight,(column-1)*blockwidth:column*blockwidth] = blankblock
    return blankimg



def main():
    '''
    Main function
    :return: None
    '''
    img = cv2.imread('selfie.jpg')
    request = int(raw_input("Press 1 for testing face detection, 2 to skip : "))
    if request == 1:
        readCamera()
    elif request == 2:
        avgImg,Facevector,difference = EigenVector(0.9)
        inputImg = cv2.imread('Keyface3.pgm',0)
        if Recognize(np.mat(inputImg).flatten(), Facevector,avgImg,difference) == True:
            print "Face recognized"
            print "Owner confirmed"
            print "Welcome! Your Majesty!"
            command = int(raw_input("Press 1 to encrypt, press 2 to decrypt, press 3 to exit"))
            encrypted = cv2.imread('Encrypted.jpg')
            if command == 1:
                encrypted,key1,key2 = encrypt(img)
                print "Key obtained"
                keyfile = open('keyholder','w')
                keyfile.write('%s'%key1)
                keyfile.write('%s'%key2)
                keyfile.close()
                print "Your encrypted image will show below"
                cv2.imshow('Encrypted',encrypted)
                cv2.imwrite('Encrypted.jpg',encrypted)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
            elif command == 2:
                try:
                    keylist1 = []
                    keylist2 = []
                    keyfile = open('keyholder','r')
                    key = keyfile.readline().replace('[',',').replace(']',',').split(',')
                    for i in key[1:101]:
                        keylist1.append(int(i))
                    for i in key[102:202]:
                        keylist2.append(int(i))
                    decrypted = decrypt(encrypted,keylist1,keylist2)
                    print "Using key to decrypt"
                    print "Your decrypted image will show below"
                    cv2.imshow('Decrypted',decrypted)
                    cv2.imwrite('Decrypted.jpg',decrypted)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
                except:
                    print "No encrypted images found"
            elif command == 3:
                print "Program exiting..."

        else:
            print "Face not recognized"
            print "Access denied"
            print "Lier!"
            print "Exiting..."


if __name__ == '__main__':
    main()