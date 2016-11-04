#coding:utf-8
from __future__ import division
import os
import sys
import random
import re
import CRFPP
import tools
import math

reload(sys)
sys.setdefaultencoding('utf8')

class Entity(object):
	def __init__(self, con, start, end, t):
		self.content = con
		self.start_pos = start
		self.end_pos = end
		self.enttype = t

def test(model, testdata, testresult):
	if not os.path.isfile(model):
		print 'Did not find the model named ' + model + '.'
		exit(-1)

	os.system('crf_test -m ' + model + ' ' + testdata + ' > ' + testresult)
	print 'Testresult ' + testresult + ' generated.' 

#CRF training
def train(template, traindata, model):
	if not os.path.isfile(traindata):
		print 'Did not find trainning data named ' + traindata + '.'
		exit(-1)		
	os.system('crf_learn -f 1 -c 2 -p 20 ' + template + ' ' + traindata + ' ' + model + ' > ' + logfile)
	print 'Model ' + model + ' generated.'

root = sys.path[0]
datafolder = os.path.join(root, 'data')
samplefolder = os.path.join(datafolder, 'gold')
modelfolder = os.path.join(root, 'models')
tempfolder = os.path.join(root, 'temp')
template = os.path.join(root, 'template')
logfile = os.path.join(tempfolder, 'log.log')
##############undo
def calculateCharRate(select_indexes, pool_indexes, index_dic, datalines):
	char_select_dic = {}	#{char1:[index1, index2, ...], char2:[index3,...]}
	char_pool_dic = {}	#{char1:[index1, index2, ...], char2:[index3,...]}
	for index in select_indexes:
		begin, end = index_dic[index]
		for line_i in range(begin, end):
			char = datalines[line_i].split('\t')[0]
			tools.addCharInDic(char, char_select_dic, index)
	for index in pool_indexes:
		begin, end = index_dic[index]
		for line_i in range(begin, end):
			char = datalines[line_i].split('\t')[0]
			tools.addCharInDic(char, char_pool_dic, index)
	
	return char_select_dic, char_pool_dic

def selectDocByTfidf(select_sentence_index, pool_sentence_index, index_dic, datalines, model, n):
	tagger = CRFPP.Tagger("-m " + model + " -v 3 -n2")
	dic_sentence_entropy = []
	select_rate_dic, pool_rate_dic = calculateCharRate(select_sentence_index, pool_sentence_index, index_dic, datalines)
	len_select, len_pool = len(select_sentence_index), len(pool_sentence_index)

	signalset = '\r\n\t !@#￥%……&*()_+{}|:"<>?,./;:\'[]\\-=！@#￥%……&×（）——+；：’“《》？，。/、|有无的'
	max_select_rate = max([len(select_rate_dic[k]) for k in select_rate_dic.keys() if k not in signalset]) / len(select_sentence_index)
	
	for index in pool_sentence_index:
		begin, end = index_dic[index]
		tagger.clear()
		for line in datalines[begin: end]:
			words = line.split('\t')
			newLine = '\t'.join(words[:-1])
			tagger.add(newLine)
		tagger.parse()
		
		ysize = tagger.ysize()	#tag1 tag2 tag3...
		size = tagger.size()	#char1 char2 char3...
		
		entropy = 0.0
		k = 1
		for i in range(0, size):
			wordCurr = tagger.x(i, 0)
			tagCurr = tagger.y2(i)
			if tagCurr == 'O':
				continue
			else:
				char_entropy = 0.0		
				for j in range(0, ysize):
					prob = tagger.prob(i, j)
					char_entropy -= prob * math.log(prob) / math.log(2)
				if select_rate_dic.has_key(wordCurr): 
					rate_in_pool = len(pool_rate_dic[wordCurr])/len_pool
					#rate_in_select = len(select_rate_dic[wordCurr]) / len_select
					#tfidf = rate_in_pool - rate_in_select
					tfidf = rate_in_pool
				else:
					rate_in_pool = len(pool_rate_dic[wordCurr])/len_pool
					tfidf = rate_in_pool
				
				#Chinese/English OR signal
				if wordCurr not in signalset:
					#char_entropy = char_entropy * ((tfidf + max_select_rate) ** k)
					char_entropy = char_entropy * ((tfidf) ** k)
				else:
					char_entropy = 0

				entropy += char_entropy
			
		#entropy /= size
		dic_sentence_entropy.append((index, entropy))
	
	dic_sentence_entropy.sort(key = lambda x:x[1], reverse = True)

	if len(dic_sentence_entropy) > n:
		return [x[0] for x in dic_sentence_entropy[:n]] 
	else:
		return [x[0] for x in dic_sentence_entropy] 

def selectDocByEntropy(pool_sentence_index, index_dic, datalines, model, n):
	tagger = CRFPP.Tagger("-m " + model + " -v 3 -n2")
	dic_sentence_entropy = []
	for index in pool_sentence_index:
		begin, end = index_dic[index]
		tagger.clear()
		for line in datalines[begin: end]:
			words = line.split('\t')
			newLine = '\t'.join(words[:-1])
			tagger.add(newLine)
		tagger.parse()
		
		ysize = tagger.ysize()	#tag1 tag2 tag3...
		size = tagger.size()	#char1 char2 char3...
		
		entropy = 0.0
		for i in range(0, size):
			#wordCurr = tagger.x(i, 0)
			#tagCurr = tagger.y2(i)			
			for j in range(0, ysize):
				prob = tagger.prob(i, j)
				entropy -= prob * math.log(prob) / math.log(2)
		#entropy /= size
		dic_sentence_entropy.append((index, entropy))
	
	dic_sentence_entropy.sort(key = lambda x:x[1], reverse = True)

	if len(dic_sentence_entropy) > n:
		return [x[0] for x in dic_sentence_entropy[:n]] 
	else:
		return [x[0] for x in dic_sentence_entropy] 

def main():
	all_sentence_file = os.path.join(datafolder, 'all_all_data')
	# trainsetfile = os.path.join(datafolder, 'all_train_data')
	# testsetfile = os.path.join(datafolder, 'all_test_data')
	# poolsetfile = os.path.join(datafolder, 'all_pool_data')

	sentencelines, sentence_index_dic = tools.getSentenceIndex(all_sentence_file)
	all_set = range(len(sentence_index_dic))
	random.shuffle(all_set)

	sizeoftest = len(sentence_index_dic) // 5
	testset, trainset = all_set[:sizeoftest], all_set[sizeoftest:]

	testfile = os.path.join(tempfolder, 'test_crf_data')
	testfile_out = open(testfile, 'w')
	for index in testset:
		begin, end = sentence_index_dic[index]
		for line_i in range(begin, end):
			testfile_out.write(sentencelines[line_i])
	testfile_out.close()

	# TRAINFILE = os.path.join(tempfolder, 'train_crf_data')
	# TRAINFILE_out = open(TRAINFILE, 'w')
	# for index in trainset:
	# 	begin, end = sentence_index_dic[index]
	# 	for line_i in range(begin, end):
	# 		testfile_out.write(sentencelines[line_i])
	# TRAINFILE_out.close()

	size_of_first_train = 50
	selectset, poolset = trainset[:size_of_first_train], trainset[size_of_first_train:]

	firsttrainfile = os.path.join(tempfolder, 'train_crf_data_0')
	with open(firsttrainfile, 'w') as firsttrainfile_out:
		for index in selectset:
			begin, end = sentence_index_dic[index]
			for line_i in range(begin, end):
				firsttrainfile_out.write(sentencelines[line_i])

	model_0 = os.path.join(tempfolder, 'model_0')
	train(template, firsttrainfile, model_0)

	testresult_0 = os.path.join(tempfolder, 'testresult_0')
	test(model_0, testfile, testresult_0)

	eval_0 = os.path.join(tempfolder, 'eval_0')
	os.system('python conlleval.py ' + testresult_0 + ' ' + eval_0)
	
	looptimes = 10
	size_of_active = 20

	#tfidf
	s, p = selectset[:], poolset[:]
	for index in range(1, looptimes+1):	#model for selecting active data
		if index == 1:
			model = model_0
		else:
			model = os.path.join(tempfolder, 'model_tfidf_' + str(index-1))

		chosen = selectDocByTfidf(s, p, sentence_index_dic, sentencelines, model, size_of_active)
		s.extend(chosen)	#new selectset

		# for line_i in chosen:
		# 	print line_i, ':', sentence_index_dic[line_i], 
		# print ''
		p = [x for x in p if x not in chosen]	#new poolset

		trainfile = os.path.join(tempfolder, 'train_tfidf_data_'+str(index))
		with open(trainfile, 'w') as trainfile_out:
			for sentence_i in s:
				begin, end = sentence_index_dic[sentence_i]
				for line_i in range(begin, end):
					trainfile_out.write(sentencelines[line_i])

		new_model = os.path.join(tempfolder, 'model_tfidf_' + str(index))
		train(template, trainfile, new_model)
		new_testresult = os.path.join(tempfolder, 'testresult_tfidf_' + str(index))
		test(new_model, testfile, new_testresult)

		new_eval = os.path.join(tempfolder, 'eval_tfidf_'+str(index))
		os.system('python conlleval.py ' + new_testresult + ' ' + new_eval)		

	#common
	s, p = selectset[:], poolset[:]
	for index in range(1, looptimes+1):	#model for selecting active data
		if index == 1:
			model = model_0
		else:
			model = os.path.join(tempfolder, 'model_common_' + str(index-1))

		chosen = selectDocByEntropy(p, sentence_index_dic, sentencelines, model, size_of_active)
		s.extend(chosen)	#new selectset
		# for line_i in chosen:
		# 	print line_i, ':', sentence_index_dic[line_i], 
		# print ''
		p = [x for x in p if x not in chosen]	#new poolset

		trainfile = os.path.join(tempfolder, 'train_common_data_'+str(index))
		with open(trainfile, 'w') as trainfile_out:
			for sentence_i in s:
				begin, end = sentence_index_dic[sentence_i]
				for line_i in range(begin, end):
					trainfile_out.write(sentencelines[line_i])

		new_model = os.path.join(tempfolder, 'model_common_' + str(index))
		train(template, trainfile, new_model)
		new_testresult = os.path.join(tempfolder, 'testresult_common_' + str(index))
		test(new_model, testfile, new_testresult)

		new_eval = os.path.join(tempfolder, 'eval_common_'+str(index))
		os.system('python conlleval.py ' + new_testresult + ' ' + new_eval)		

	#random
	'''
	s, p = selectset[:], poolset[:]
	for index in range(1, looptimes+1):	#model for selecting active data
		if index == 1:
			model = model_0
		else:
			model = os.path.join(tempfolder, 'model_random_' + str(index-1))

		random.shuffle(p)
		chosen = p[:size_of_active]
		s.extend(chosen)	#new selectset

		p = [x for x in p if x not in chosen]	#new poolset
		trainfile = os.path.join(tempfolder, 'train_random_data_'+str(index))
		with open(trainfile, 'w') as trainfile_out:
			for sentence_i in s:
				begin, end = sentence_index_dic[sentence_i]
				for line_i in range(begin, end):
					trainfile_out.write(sentencelines[line_i])

		new_model = os.path.join(tempfolder, 'model_random_' + str(index))
		train(template, trainfile, new_model)
		new_testresult = os.path.join(tempfolder, 'testresult_random_' + str(index))
		test(new_model, testfile, new_testresult)

		new_eval = os.path.join(tempfolder, 'eval_random_'+str(index))
		os.system('python conlleval.py ' + new_testresult + ' ' + new_eval)		
	'''
	tools.evalCompare(looptimes, tempfolder, 'eval_random_', 'eval_common_', 'eval_tfidf_')	

if __name__ == '__main__':
	main()