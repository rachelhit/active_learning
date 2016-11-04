#coding:utf8
import re
import sys
import os
import random

class Entity(object):
	def __init__(self, con, start, end, t):
		self.content = con
		self.start_pos = start
		self.end_pos = end
		self.enttype = t

#split sentence in in_file
#@param:
#	infile: xml file
#	outfile: output file, with suffix of '.sen'
def split_sentence(in_file, out_file):
	text = open(in_file).read().decode('utf-8').replace('\r', '')
	out_file = open(out_file, 'w')
	sentence = ''
	sentence_list = []

	#split
	for i, token in enumerate(text):
		sentence += token
		if token == u'.':
			if i > 0 and i < len(text) - 2:
				if not text[i - 1].isdigit() or not text[i + 1].isdigit():
					if text[i + 1] == u' ' and text[i + 2].isdigit():
						continue
					sentence_list.append('%s###%s###%s' % ( sentence.encode('utf8'), i - len(sentence) + 1, i + 1))
					sentence = ''

		elif token in u'。；\n;':
			if token == u'\n':
				sentence = sentence[:-1]
				sentence_list.append('%s###%s###%s' % (sentence.encode('utf8'), i - len(sentence), i))

			else:
				sentence_list.append('%s###%s###%s' % ( sentence.encode('utf8'), i - len(sentence) + 1, i + 1))
			
			sentence = ''

	#get title of each sentence
	for i in range(2):
		sentence_list[i] += '###NONE\n'

	i = 2
	title = ''
	while i < len(sentence_list) - 1:
		sen = sentence_list[i].split('###')[0]
		match_result = re.findall(ur'</(.+)>', sen)
		if match_result:
			sentence_list[i] += '###%s\n'%title
		else:
			match_result = re.match(ur'\s*<(.+)>', sen)
			if match_result:
				title = match_result.group(1)
			sentence_list[i] += '###%s\n'%title
		i += 1
	sentence_list[i] += '###NONE\n'
	out_file.writelines(sentence_list)
	out_file.close()

def get_sentence_entity(sen_file, ent_file):
	with open(sen_file) as sen_f:
		sen_list = sen_f.readlines()
	with open(ent_file) as ent_f:
		ent_list = ent_f.readlines()

	sen_ent = {}
	i = 0
	untagged = 0

	for j, sen in enumerate(sen_list):
		if len(sen.strip().split('###')[0]) <= 2:
			continue
		if sen[:-1].find('<诊断依据>') != -1: untagged = 1
		if sen[:-1].find('</鉴别诊断>') != -1: untagged = 0

		sentence = sen[:-1].split('###')[0]
		if sentence == '' or (sentence.find('<') != -1 and sentence.find('>') != -1) or untagged == 1: continue # 跳过标记行

		sen_start = int(sen[:-1].split('###')[1])
		sen_end = int(sen[:-1].split('###')[2])
		title = sen[:-1].split('###')[3]
		key = sentence + '###%s###%s'%(title, sen_start)
		if key not in sen_ent:
			sen_ent[key] = []
		while i < len(ent_list):
			content, ent_start, ent_end, enttype = re.findall('C=(.*) P=(\d+):(\d+) T=(\w+).*', ent_list[i])[0]
			ent_start, ent_end = int(ent_start), int(ent_end)
			i += 1
			if ent_start >= sen_start and ent_end <= sen_end:
				sen_ent[key].append(Entity(content, ent_start - sen_start, ent_end - sen_start, enttype))
			elif ent_end < sen_start:
				continue
			elif ent_start > sen_end:
				i -= 1
				break
	return sen_ent

# replace signals with Chinese signal
def uniform(inLine):
	inLine = inLine.replace(",","，") # 替换中英标点
	inLine = inLine.replace("(","（")
	inLine = inLine.replace(")","）")
	inLine = inLine.replace(";","；")
	inLine = inLine.replace(":","：")
	inLine = inLine.replace('#','$')
	inLine = inLine.replace('×','*')
	inLine = inLine.replace('μ','u')
	inLine = inLine.replace('β','B')
	inLine = inLine.replace('γ','r')
	inLine = inLine.replace('°C','℃ ')
	inLine = inLine.replace('°c','℃ ')
	inLine = inLine.replace('°','度')
	return inLine

# seg sentence s with model seg_model
def segment(s, seg_model, temppath):
	segfilepre = os.path.join(temppath, 'seg_pre.temp')
	segfiletag = os.path.join(temppath, 'seg_tag.temp')

	segfilepre_w = open(segfilepre, 'w')
	parts = s.strip().split(' ')
	for x in parts:
		tblocks = []
		x = x.decode('utf8')
		for y in x:
			tblocks.append(y.encode('utf8'))
		for i in range(0, len(tblocks)):
			segfilepre_w.write(tblocks[i] + '\n')
	segfilepre_w.close()

	os.system('crf_test -m ' + seg_model + ' ' + segfilepre + ' > ' + segfiletag)

	segfiletag_f = open(segfiletag, 'r')
	lines = segfiletag_f.read().strip().split('\n')
	segfiletag_f.close()

	tokens = []
	token = ''
	seg_length = len(lines)
	for i in range(seg_length):
		if len(lines[i]) <= 1: break
		parts = lines[i].split('\t')
		if parts[1] == 'S':
			tokens.append(parts[0])
			token = ''
			continue
		if parts[1] == 'B' or parts[1] == 'M':
			token += parts[0]
			continue
		if parts[1] == 'E':
			token += parts[0]
			tokens.append(token)
			token = ''
			continue
	s_seg = ''
	for j in range(len(tokens)):
		s_seg += tokens[j] + ' '
	return s_seg

#get seg tags of characters after segment
def getSegmentTags(sentence, sen_seg):
	tags = []
	sen_unicode = sentence.replace(' ', '').decode('utf8')
	tokens = sen_seg.split(' ')
	for i in range(len(tokens)):
		token = tokens[i].decode('utf8')
		if len(token) == 0:
			continue
		if len(token) == 1:
			tags.append('S')
			continue
		else:
			tags.append('B')
			for j in range(1, len(token)-1):
				tags.append('I')
			tags.append('E')
	if len(tags) != len(sen_unicode):
		exit(-1)
	else:
		return tags

# pos
def pos(seg, pos_model, temppath):
	posfilepre = os.path.join(temppath, 'pos_pre.temp')
	posfiletag = os.path.join(temppath, 'pos_tag.temp')

	posfilepre_f = open(posfilepre, 'w')
	cblocks = seg.strip().split(' ')
	pre = ''
	suf = ''

	for i in range(0,len(cblocks)) :
		pn = len(cblocks[i].decode('utf8'))
		pre = cblocks[i].decode('utf8')[0].encode('utf8')
		suf = cblocks[i].decode('utf8')[-1].encode('utf8')
		posfilepre_f.write(cblocks[i] + '\t' + pre + '\t' + suf + '\t' + str(pn) + '\n')
	posfilepre_f.close()

	os.system('crf_test -m ' + pos_model + ' ' + posfilepre + ' > ' + posfiletag)

	posfiletag_f = open(posfiletag, 'r')
	lines = posfiletag_f.read().strip().split('\n')
	posfiletag_f.close()

	s_token = []
	s_pos = []
	for i in range(len(lines)):
		if len(lines[i]) <= 1: break
		parts = lines[i].split('\t')
		s_token.append(parts[0])
		s_pos.append(parts[-1])
	return s_token, s_pos

def getPosTags(sentence, tokens, postags):
	tags = []
	for i in range(len(tokens)):
		token = tokens[i].decode('utf8')
		for j in range(len(token)):
			tags.append(postags[i])

	if len(tags) != len(sentence.replace(' ', '').decode('utf8')):
		print sentence
		print tags
		exit(-1)

	return tags

def getEntityTags(sentence, entities):
	tags = [ 'O' for i in range(len(sentence.decode('utf8')))]
	for ent in entities:
		start, end, enttype = ent.start_pos, ent.end_pos, ent.enttype
		if end - start == 1:
			tags[start] = 'S-' + enttype
			continue
		else:
			tags[start] = 'B-' + enttype
			for i in range(start+1, end-1):
				tags[i] = 'I-' + enttype
			tags[end-1] = 'E-' + enttype
	return tags

def getFilenames(samplefolder):
	filenames = []
	for root, dirs, files in os.walk(samplefolder):
		for file in files:
			if file.endswith('xml') == False : continue
			filenames.append(file[:-4])
	return filenames
	
def divideInto2Groups(filenames, first_group_size):
	num_of_files = len(filenames)
	if num_of_files <= first_group_size:
		group1 = filenames
		group2 = []
	else:
		random.shuffle(filenames)
		group1 = filenames[:first_group_size]
		group2 = filenames[first_group_size:]
	return group1, group2

#dic:{char1:times, char2:times, ...}
#dic:{char1:[filename1, filename2,...], char2:[filename3, filename4,...], ...}
def addCharInDic(char, dic, filename='null'):
	if filename == 'null':
		if dic.has_key(char):
			dic[char] += 1
		else:
			dic[char] = 1
	else:
		if dic.has_key(char):
			if filename not in dic[char]:
				dic[char].append(filename)
		else:
			dic[char] = [filename]		

def evalCompare(active_times, tempfolder, random_eval_name, common_eval_name, tfidf_eval_name):
	eval_file = os.path.join(tempfolder, 'eval_0')
	with open(eval_file, 'r') as f:
		data = f.readlines()[-1]
		print 'Origin eval:'
		print data
	with open('eval.txt', 'w') as fo:
		fo.write('Origin eval:\n')
		fo.write(data)
		for i in range(1, active_times+1):
			fo.write(str(i) + ':\n')
			'''
			eval_file = os.path.join(tempfolder, random_eval_name+str(i))
			with open(eval_file, 'r') as f:
				data = f.readlines()[-1]
				print 'Random active ' + str(i) + ':' 
				print data
				fo.write('Random active ' + str(i) + ':\n')
				fo.write(data)
			'''
			eval_file = os.path.join(tempfolder, common_eval_name+str(i))
			with open(eval_file, 'r') as f:
				data = f.readlines()[-1]
				print 'Common active ' + str(i) + ':' 
				print data
				fo.write('Common active ' + str(i) + ':\n' )
				fo.write(data)
			eval_file = os.path.join(tempfolder, tfidf_eval_name+str(i))
			with open(eval_file, 'r') as f:
				data = f.readlines()[-1]
				print 'TFIDF active ' + str(i) + ':' 
				print data
				fo.write('TFIDF active ' + str(i) + ':\n' )
				fo.write(data)

def getSentenceIndex(poolsetfile):
	sentence_dic = {}
	sentence_index = 0
	with open(poolsetfile, 'r') as f:
		line = f.readline()
		begin, end = 0, 0
		while line:
			if line.strip() == '':
				end += 1	#line'\n' include
				sentence_dic[sentence_index] = (begin, end)
				begin = end
				sentence_index += 1
			else:
				end += 1
			line = f.readline()	

	with open(poolsetfile, 'r') as f:
		poolsetfilelines = f.readlines()
	return poolsetfilelines, sentence_dic