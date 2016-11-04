#python genSet.py num_of_test num_of_first_train
import tools
import newmain
import sys
import os

root = sys.path[0]
datafolder = os.path.join(root, 'data')
samplefolder = os.path.join(datafolder, 'gold')
modelfolder = os.path.join(root, 'models')
tempfolder = os.path.join(root, 'temp')
template = os.path.join(root, 'template')

def main():
	filenames = tools.getFilenames(samplefolder)

	#trainset & testset
	sizeoftest = int(sys.argv[1])
	
	testset, trainset = tools.divideInto2Groups(filenames, sizeoftest)
	
	testfile = os.path.join(datafolder, 'all_test_data')
	testfile_out = open(testfile, 'w')
	for filename in testset:		
		newmain.write2traindata(os.path.join(samplefolder,filename), modelfolder, tempfolder, testfile_out)
	testfile_out.close()

	size_of_first_train = int(sys.argv[2])
	selectset, poolset = tools.divideInto2Groups(trainset, size_of_first_train)	
	trainfile = os.path.join(datafolder, 'all_train_data')
	trainfile_out = open(trainfile, 'w')
	for filename in selectset:
		newmain.write2traindata(os.path.join(samplefolder,filename), modelfolder, tempfolder, trainfile_out)
	trainfile_out.close()

	poolfile = os.path.join(datafolder, 'all_pool_data')
	poolfile_out = open(poolfile, 'w')
	for filename in poolset:
		newmain.write2traindata(os.path.join(samplefolder,filename), modelfolder, tempfolder, poolfile_out)
	poolfile_out.close()

	allfile = os.path.join(datafolder, 'all_all_data')
	allfile_out = open(allfile, 'w')
	for filename in filenames:
		newmain.write2traindata(os.path.join(samplefolder,filename), modelfolder, tempfolder, allfile_out)
	allfile_out.close()
	
if __name__ == '__main__':
	main()