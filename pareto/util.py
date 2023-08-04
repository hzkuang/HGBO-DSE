import os


def getListPPA(path):
    listPPA = []
    for file in os.listdir(path):
        if file.split('_')[0] == 'ppa':
            file_path = os.path.join(path, file)
            listPPA.append(file_path)
    listPPA.sort(key=lambda x: (int((x.split('_')[-1]).split('.')[0])))
    return listPPA


def multiplyList(myList):
    result = 1
    for x in myList:
        result = result * x
    return result
