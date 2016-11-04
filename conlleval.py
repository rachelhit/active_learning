#coding=utf-8

import sys

def getSameCount(l1,l2):
	i1 = 0
	i2 = 0
	count = 0
	while i1 < len(l1) and i2 < len(l2):
		if l1[i1] == l2[i2]:
			count = count + 1
			i1 = i1 + 1
			i2 = i2 + 1
		else:
			if l1[i1][0] < l2[i2][0]:
				i1 = i1 + 1
			elif l1[i1][0] > l2[i2][0]:
				i2 = i2 + 1
			else:
				i1 = i1 + 1
				i2 = i2 + 1
	return count

def conlleval():
	try:
		result = open(sys.argv[2],'w')
	except:
		sys.stderr("infile not existed!")
		sys.exit("-1")
	disease = getList('disease')
	diseaseType = getList('diseasetype')
	complain = getList('complaintsymptom')
	testResult = getList('testresult')
	test = getList('test')
	treatment = getList('treatment')
	result.writelines('entity\tTP\tFP\tFN\tP\tR\tF\n')
	result.writelines(disease)
	result.writelines(diseaseType)
	complain2 = complain.split('\t')
	testResult2 = testResult.split('\t')
	symptom = 'symptom'+'\t'+getF(int(complain2[1])+int(testResult2[1]),int(complain2[2])+int(testResult2[2]),int(complain2[3])+int(testResult2[3]))
#	names=['complaintsymptom','testresult']
#	symptom = getList2(names)
	result.writelines(symptom)
	result.writelines(complain)
	result.writelines(testResult)
	result.writelines(test)
	result.writelines(treatment)
	lis = [disease,diseaseType,symptom,test,treatment]
	result.writelines('MicroP\tMicroR\tMicroF\n')
	result.writelines(getM(lis))
	result.close()


def getList(name):	
	try:
		#print(sys.argv[1])
		test = open(sys.argv[1])
	except:
		sys.stderr("infile not existed!")
		sys.exit("-1")
	lis = [[],[]]
	current = 0
	start = [-1,-1]
	count = [-1,-1]
	entity = ['','']
	for line in test:
		if line.strip() == '':
			current = current + 1
			continue
		line2 = line.strip().split('\t')
		for i in range(2):
			if start[i] == -1:
				if line2[len(line2)-2+i] == 'B-' + name:
					start[i] = current
					count[i] = 1
					entity[i] = line2[len(line2)-2+i]
			else:
				if line2[len(line2)-2+i] == 'I-' + name:
					count[i] = count[i] + 1
				else:
					tmp = [start[i],count[i]]
#					print('current:'+str(current)+'   i:'+str(i)+'  start:'+str(start[i])+'   len:'+str(count[i]))
					lis[i].append(tmp)
					if line2[len(line2)-2+i] == 'B-' + name:
						start[i] = current
						count[i] = 1
						entity[i] = line2[len(line2)-2+i]
					else:
						start[i] = -1
						count[i] = 1
						entity[i] = ''
#			if line2[2+i] == 'O':
#				if not(start[i] == -1):
#					tmp = [start[i],count[i]]
#					if entity[i] == name+'_B':
#						lis[i].append(tmp)
#					start[i] = -1
#					count[i] = 1
#					entity[i] = ''
#			else:
#				if start[i] == -1:
#					start[i] = current
#					count[i] = 1
#					entity[i] = line2[2+i]
#				else:
#					count[i] = count[i] + 1
		current = current + 1
#	print(lis[0])
#	print(len(lis[1]))
	TP = getSameCount(lis[0],lis[1])
	FP = len(lis[1]) - TP
	FN = len(lis[0]) - TP
	#print(TP)
	#print(FP)
	#print(FN)
	result = name+'\t'+getF(TP,FP,FN)
	test.close()
	return result


def getList2(names):
	lis = [[],[]]
	try:
		test = open(sys.argv[1])
	except:
		sys.stderr("infile not existed!")
		sys.exit("-1")
#	lis = [[],[]]
#	print(names[k])
	current = 0
	start = [[-1,-1],[-1,-1]]
	count = [[-1,-1],[-1,-1]]
	entity = [['',''],['','']]
	for line in test:
		if line.strip() == '':
			current = current + 1
			continue
		line2 = line.strip().split('\t')
		for i in range(2):
			for k in range(len(names)):
				if start[k][i] == -1:
					if line2[len(line2)-2+i] == 'B-' + names[k]:
						start[k][i] = current
						count[k][i] = 1
						entity[k][i] = line2[len(line2)-2+i]
				else:
					if line2[len(line2)-2+i] == 'I-' + names[k]:
						count[k][i] = count[k][i] + 1
					else:
						tmp = [start[k][i],count[k][i]]
						lis[i].append(tmp)
						if line2[len(line2)-2+i] == 'B-' + names[k]:
							start[k][i] = current
							count[k][i] = 1
							entity[k][i] = line2[len(line2)-2+i]
						else:
							start[k][i] = -1
							count[k][i] = 1
							entity[k][i] = ''
		current = current + 1
	print(len(lis[0]))
	print(len(lis[1]))	
	TP = getSameCount(lis[0],lis[1])
	FP = len(lis[1]) - TP
	FN = len(lis[0]) - TP
	print(TP)
	print(FP)
	print(FN)
	result = 'symptom\t'+getF(TP,FP,FN)
	test.close()
	return result


def getF(TP,FP,FN):
	e = 0.0001
	P = round(1.0*TP/(TP+FP+e),4)
	R = round(1.0*TP/(TP+FN+e),4)
	#F = round(2.0*P*R/(R+P+e),4)
	F = 2*P*R/(P+R+e)
	s = str(TP)+'\t'+str(FP)+'\t'+str(FN)+'\t'+str(P)+'\t'+str(R)+'\t'+str(F)+'\n'
	return s


def getM(lis):
	MicroP = 0
	MicroR = 0
	MicroF = 0
	TP = 0
	FP = 0
	FN = 0
	e = 0.0001
	for i in range(len(lis)):
		lis2 = lis[i].split('\t')
		TP = TP + int(lis2[1])
		FP = FP + int(lis2[2])
		FN = FN + int(lis2[3])

	MicroP = round(1.0*TP/(TP+FP+e),4)
	MicroR = round(1.0*TP/(TP+FN+e),4)
	if MicroP + MicroR == 0:
		MicroF = 'NaN'
	else:
		MicroF = round(2.0*MicroP*MicroR/(MicroR+MicroP),4)
	s = str(MicroP)+'\t'+ str(MicroR)+'\t'+ str(MicroF)+'\n'
	return s

# python conlleval.py $pcPath/testInfo $pcPath/conlleval
if __name__=="__main__":
	conlleval()
