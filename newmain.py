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
	outputlog = os.path.join(tempfolder, 'train.log')
	os.system('crf_learn -f 1 -c 2 -p 20 ' + template + ' ' + traindata + ' ' + model + ' > ' + outputlog)
	print 'Model ' + model + ' generated.'

def write2traindata(filename, modelfolder, tempfolderpath, output):
	in_file = filename + '.xml'
	sen_file = in_file + '.sen'
	ent_file = in_file + '.ent'
	tools.split_sentence(in_file, sen_file)
	dic_sen_ent = tools.get_sentence_entity(sen_file, ent_file)

	seg_model = os.path.join(modelfolder, 'segmenter.model')
	pos_model = os.path.join(modelfolder, 'postagger.model')

	for k, v in dic_sen_ent.items():
		if len(v) == 0:
			continue

		entities = sorted(v, key = lambda ent:ent.start_pos)
		sentence, title = k.split('###')[:2]
		sentence_input = sentence.replace('\t', ' ')
		sentence_input = sentence_input.replace('\r\n', '')
		sentence_uniform = tools.uniform(sentence_input)

		sentence_seg = tools.segment(sentence_uniform, seg_model, tempfolderpath)
		seg_tags = tools.getSegmentTags(sentence_uniform, sentence_seg)

		words, postags = tools.pos(sentence_seg, pos_model, tempfolderpath)
		pos_tags = tools.getPosTags(sentence_uniform, words, postags)

		ent_tags = tools.getEntityTags(sentence_uniform, entities)
		
		#character, seg_tag, pos_tag, ent_tag
		sentence_unicode = sentence_uniform.decode('utf8')
		j = 0
		for i in range(len(sentence_unicode)):
			if sentence_unicode[i] == ' ':
				continue
			else:
				output.write('%s\t%s\t%s\t%s\n' % (sentence_unicode[i], seg_tags[j], seg_tags[j]+'-'+pos_tags[j], ent_tags[i]))
				j += 1
		output.write('\n')

def calculateCharRate(filename_list):
	char_dic = {}
	char_filename_dic = {}
	for filename in filename_list:
		file = os.path.join(samplefolder, filename+'.crf')
		with open(file, 'r') as f:
			lines = f.readlines()
			for line in lines:
				if line.strip() == '':
					continue
				else:
					char = line.split('\t')[0]
					tools.addCharInDic(char, char_dic)
					tools.addCharInDic(char, char_filename_dic, filename)
	return char_dic, char_filename_dic


def selectDocByTfidf(trainset, poolset, model, n):
	chosen = []
	char_dic, char_filename_dic = calculateCharRate(poolset)

	tagger = CRFPP.Tagger("-m " + model + " -v 3 -n2")
	dic_filename_entropy = []
	for filename in poolset:
		tagger.clear()
		f = open(os.path.join(samplefolder, filename+'.crf'), 'r')
		entropy_sum = 0.0
		line_num = 0
		line = f.readline()
		while line:
			if len(line.strip()) <= 1:
				tagger.parse()
				ysize = tagger.ysize()	#tag1 tag2 tag3...
				size = tagger.size()	#char1 char2 char3...
				
				entropy = 0.0
				for i in range(0, size):
					wordCurr = tagger.x(i, 0)
					word_entropy = 0.0
					rate = len(char_filename_dic[wordCurr])
					tagCurr = tagger.y2(i)
					
					for j in range(0, ysize):
						prob = tagger.prob(i, j)
						word_entropy -= prob * math.log(prob) / math.log(2)
					entropy += word_entropy * rate

				entropy /= size
					
				tagger.clear()
				line_num += 1
				entropy_sum += entropy

				line = f.readline()
			else:
				words = line.split('\t')
				newLine = '\t'.join(words[:-1])
				tagger.add(newLine)
				line = f.readline()
		entropy_sum /= line_num
		dic_filename_entropy.append((filename, entropy_sum))

		f.close()
	
	dic_filename_entropy.sort(key = lambda x:x[1], reverse = True)

	if len(dic_filename_entropy) > n:
		return [x[0] for x in dic_filename_entropy[:n]] 
	else:
		return [x[0] for x in dic_filename_entropy] 
	

def selectDocByEntropy(trainset, poolset, model, n):
	tagger = CRFPP.Tagger("-m " + model + " -v 3 -n2")
	dic_filename_entropy = []
	for filename in poolset:
		tagger.clear()
		f = open(os.path.join(samplefolder, filename+'.crf'), 'r')
		entropy_sum = 0.0
		line_num = 0
		line = f.readline()
		while line:
			if len(line.strip()) <= 1:
				tagger.parse()
				ysize = tagger.ysize()	#tag1 tag2 tag3...
				size = tagger.size()	#char1 char2 char3...
				
				entropy = 0.0
				for i in range(0, size):
					wordCurr = tagger.x(i, 0)
					tagCurr = tagger.y2(i)
					
					for j in range(0, ysize):
						prob = tagger.prob(i, j)
						entropy -= prob * math.log(prob) / math.log(2)
				entropy /= size
				
				tagger.clear()
				line_num += 1
				entropy_sum += entropy

				line = f.readline()
			else:
				words = line.split('\t')
				newLine = '\t'.join(words[:-1])
				tagger.add(newLine)
				line = f.readline()
		entropy_sum /= line_num
		dic_filename_entropy.append((filename, entropy_sum))

		f.close()
	
	dic_filename_entropy.sort(key = lambda x:x[1], reverse = True)

	if len(dic_filename_entropy) > n:
		return [x[0] for x in dic_filename_entropy[:n]] 
	else:
		return [x[0] for x in dic_filename_entropy] 


root = sys.path[0]
datafolder = os.path.join(root, 'data')
samplefolder = os.path.join(datafolder, 'gold')
modelfolder = os.path.join(root, 'models')
tempfolder = os.path.join(root, 'temp')
template = os.path.join(root, 'template')

def main():

	#trainfile = os.path.join(tempfolder, 'trainning')
	filenames = tools.getFilenames(samplefolder)

	#trainset & testset
	sizeoftest = len(filenames) // 5
	testset, trainset = tools.divideInto2Groups(filenames, sizeoftest)
	testfile = os.path.join(tempfolder, 'test_crf_data')
	testfile_out = open(testfile, 'w')
	for filename in testset:
		write2traindata(os.path.join(samplefolder,filename), modelfolder, tempfolder, testfile_out)
	testfile_out.close()
	
	# #method with all data
	# alltrainfile = os.path.join(tempfolder, 'all_train_crf_data')
	# alltrainfile_out = open(alltrainfile, 'w')
	# for filename in trainset:
	# 	write2traindata(os.path.join(samplefolder,filename), modelfolder, tempfolder, alltrainfile_out)
	# alltrainfile_out.close()
	# model_all = os.path.join(tempfolder, 'model_all')
	# train(template, alltrainfile, model_all)
	# testresult_all = os.path.join(tempfolder, 'testresult_all')
	# test(model_all, testfile, testresult_all)
	# eval_all = os.path.join(tempfolder, 'eval_all')
	# os.system('python conlleval.py ' + testresult_all + ' ' + eval_all)

	#write each file to crf
	# for filename in filenames:
	# 	with open(os.path.join(samplefolder, filename+'.crf'), 'w') as f_out:
	# 		write2traindata(os.path.join(samplefolder, filename), modelfolder, tempfolder, f_out)

	#first train
	size_of_first_train = 100
	selectset, poolset = tools.divideInto2Groups(trainset, size_of_first_train)	

	firsttrainfile = os.path.join(tempfolder, 'train_crf_data_0')
	firsttrainfile_out = open(firsttrainfile, 'w')
	for filename in selectset:
		write2traindata(os.path.join(samplefolder, filename), modelfolder, tempfolder, firsttrainfile_out)
	firsttrainfile_out.close()
	model_0 = os.path.join(tempfolder, 'model_0')
	train(template, firsttrainfile, model_0)

	testresult_0 = os.path.join(tempfolder, 'testresult_0')
	test(model_0, testfile, testresult_0)

	eval_0 = os.path.join(tempfolder, 'eval_0')
	os.system('python conlleval.py ' + testresult_0 + ' ' + eval_0)
	
	looptimes = 2
	size_of_active = 20
	#TF-IDF method with entropy
	s, p = selectset[:], poolset[:]
	for index in range(1, looptimes+1):	#model for selecting active data
		if index == 1:
			model = model_0
		else:
			model = os.path.join(tempfolder, 'model_tfidf_' + str(index-1))

		chosen = selectDocByTfidf(s, p, model, size_of_active)
		s.extend(chosen)	#new selectset
		p = [x for x in p if x not in chosen]	#new poolset

		trainfile = os.path.join(tempfolder, 'train_tfidf_data_'+str(index))
		with open(trainfile, 'w') as trainfile_out:
			for filename in s:
				with open(os.path.join(samplefolder, filename+'.crf'), 'r') as selectfile:
					lines = selectfile.readlines()
				for line in lines:
					trainfile_out.write(line)

		new_model = os.path.join(tempfolder, 'model_tfidf_' + str(index))
		train(template, trainfile, new_model)
		new_testresult = os.path.join(tempfolder, 'testresult_tfidf_' + str(index))
		test(new_model, testfile, new_testresult)

		new_eval = os.path.join(tempfolder, 'eval_tfidf_'+str(index))
		os.system('python conlleval.py ' + new_testresult + ' ' + new_eval)		

	#common medthod with entropy
	s, p = selectset[:], poolset[:]
	for index in range(1, looptimes+1):	#model for selecting active data
		if index == 1:
			model = model_0
		else:
			model = os.path.join(tempfolder, 'model_common_' + str(index-1))

		chosen = selectDocByEntropy(s, p, model, size_of_active)
		s.extend(chosen)	#new selectset
		p = [x for x in p if x not in chosen]	#new poolset

		trainfile = os.path.join(tempfolder, 'train_common_data_'+str(index))
		with open(trainfile, 'w') as trainfile_out:
			for filename in s:
				with open(os.path.join(samplefolder, filename+'.crf'), 'r') as selectfile:
					lines = selectfile.readlines()
				for line in lines:
					trainfile_out.write(line)

		new_model = os.path.join(tempfolder, 'model_common_' + str(index))
		train(template, trainfile, new_model)
		new_testresult = os.path.join(tempfolder, 'testresult_common_' + str(index))
		test(new_model, testfile, new_testresult)

		new_eval = os.path.join(tempfolder, 'eval_common_'+str(index))
		os.system('python conlleval.py ' + new_testresult + ' ' + new_eval)	

	# random select
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
			for filename in s:
				with open(os.path.join(samplefolder, filename+'.crf'), 'r') as selectfile:
					lines = selectfile.readlines()
				for line in lines:
					trainfile_out.write(line)

		new_model = os.path.join(tempfolder, 'model_random_' + str(index))
		train(template, trainfile, new_model)
		new_testresult = os.path.join(tempfolder, 'testresult_random_' + str(index))
		test(new_model, testfile, new_testresult)

		new_eval = os.path.join(tempfolder, 'eval_random_'+str(index))
		os.system('python conlleval.py ' + new_testresult + ' ' + new_eval)	

	tools.evalCompare(looptimes, tempfolder, 'eval_random_', 'eval_common_', 'eval_tfidf_')	

if __name__ == '__main__':
	main()