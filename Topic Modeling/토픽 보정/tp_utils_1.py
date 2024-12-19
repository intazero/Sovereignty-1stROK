import pandas as pd
import sys
import numpy as np
import math
import os, re

# 코드 출처 : [Python] 단어 간 상호정보량 계산 코드
## https://bab2min.tistory.com/551

class PMICalc:
    def __init__(self, **kargs):
        self.window = kargs.get('window', 5)
        self.minNum = kargs.get('minNum', 1)
        self.dictCount = {}
        self.dictBiCount = {}
        self.searchPair = {}
        self.nTotal = 0

    def train(self, sentenceIter):
        def insertPair(a, b):
            if a > b: a, b = b, a
            elif a == b: return
            self.dictBiCount[a, b] = self.dictBiCount.get((a, b), 0) + 1
            if a in self.searchPair: self.searchPair[a].add(b)
            else: self.searchPair[a] = set([b])
            if b in self.searchPair: self.searchPair[b].add(a)
            else: self.searchPair[b] = set([a])

        for sent in sentenceIter:
            self.nTotal += len(sent)
            for i, word in enumerate(sent):
                self.dictCount[word] = self.dictCount.get(word, 0) + 1
                for j in range(i+1, len(sent)):  # min(i+self.window+1, + )
                    if sent[j] != word: insertPair(word, sent[j])

    def getCoOccurrence(self, a, b):
        if a > b: a, b = b, a
        elif a == b: return
        return self.dictBiCount.get((a, b), 0)

    def getPMI(self, a, b):
        import math
        co = self.getCoOccurrence(a, b)
        if not co: return None
        return math.log(float(co) * self.nTotal / self.dictCount[a] / self.dictCount[b])

    def getHighestPair(self, a, n = 10):
        return sorted(map(lambda b:(b, self.getPMI(a,b)), 
                          filter(lambda x:self.getCoOccurrence(a,x) >= self.minNum, 
                                 self.searchPair[a])), key=lambda x:x[1], reverse=True)[:n]

    
#  리스트에서 모든 가능한 조합의 pmi 산출   

def all_pmi_generate(topic_name, input_list):
    
    all_combi = {}
    for i in range(len(topic_name)-1):
        source = topic_name[i]
        targets = topic_name[i+1:] # source 앞 단어와는 조합하지 않음.

        for target in targets:
            pmi = pc.getPMI(source, target) # pmi 산출 함수
            combi_key = source+'_'+target
            all_combi[combi_key] = pmi
            
    return all_combi


# 리스트에서 요소간(TC간) 모든 가능한 조합 산출
def all_tcCombi_generate(sepTCs_list, tpWList):
    tcCombining_dict = {}
    
    if len(sepTCs_list) == 1: # 입력값이 리스트 요소 단 1개일 때
        (tc_name, tc_list) = (sepTCs_list[0][0], sepTCs_list[0][1])
        tcCombining_dict[tc_name] = tc_list
            
    for i in range(len(sepTCs_list)-1):
        source = sepTCs_list[i]
        targets = sepTCs_list[i+1:]

        for target in targets:
            combi_tc = list(set(source[1]+target[1]))
            arr_combi_tc = [tpw for tpw in tpWList if tpw in combi_tc] # combi를 원래 순서대로 재배열
            tcCombining_dict[source[0]+'_'+target[0][2:]] = arr_combi_tc
            
    return tcCombining_dict


def TC_generate(input_list, tpWList, pc): 

    posit_tc_dict = {}
    #1. 20개 tpw를 각각을 기준 단어로 해서 나머지 tpw와의 pmi를 산출한 뒤 양수값으로 tc를 구성 
    for (i,tpwords) in enumerate(tpWList):
        source = tpWList[i]
        targets = tpWList[i+1:] + tpWList[:i] # 기준 단어의 우측 단어부터 포함 + 좌측 단어

        tc = [source]
        stoptw = []
        for target in targets:
            if target in stoptw: continue 
            pmi = pc.getPMI(source, target) # pmi 산출 함수
            if pmi is None: stoptw.append(target)
            else: tc.append(target)
    #2. tc 단어를 본래의 tpw 순서대로 재배열 (중복 제거 위해)
        arr_tc = []
        for tw in tpWList:
            if tw in tc: arr_tc.append(tw)
        if len(str(i)) == 1: tc_name = 'tc0'+str(i) # 나중에 tc 순서대로 하기 위해 자릿수 2개로 통일
        else: tc_name = 'tc'+str(i)
        posit_tc_dict[tc_name] = arr_tc  # 딕셔너리에 결과값을 넣어 줌

    return posit_tc_dict
    

def uniquing_sepTCs(TC_generate, input_list, pc, tpWList): # tcs는 두 경우 중 1 case만 해당
    
    posit_tc_dict = TC_generate(input_list, tpWList, pc)
    
    # 딕셔너리 값(values)의 중복 제거
    new_tp_cliq = {tuple(v):k for k,v in posit_tc_dict.items()} # 리스트를 키값으로 할 경우(for 중복제거), 튜플로 바꿔야 함
    uniq_tp_cliq = {v:list(k) for k,v in new_tp_cliq.items()} # 다시 순서 역전

    # 딕셔너리 키값을 정렬해서 출력하는 코드 (딕셔너리는 간단히는 정렬 안되므로)
    key_dict = uniq_tp_cliq.keys()
    key_list = list(key_dict)
    key_list.sort() 

    sepTCs_list = []
    for key in key_list:
        result = (key, uniq_tp_cliq[key])
        if key in uniq_tp_cliq.keys(): sepTCs_list.append(result)
            
    return sepTCs_list


def uniquing_tcCombining(all_tcCombi_generate, sepTCs_list, tpWList): 
    
    tcCombining_dict = all_tcCombi_generate(sepTCs_list, tpWList) 
    
    # 딕셔너리 값(values)의 중복 제거
    new_tp_cliq = {tuple(v):k for k,v in tcCombining_dict.items()} # 리스트를 키값으로 할 경우(for 중복제거), 튜플로 바꿔야 함
    uniq_tp_cliq = {v:list(k) for k,v in new_tp_cliq.items()} # 다시 순서 역전

    # 딕셔너리 키값을 정렬해서 출력하는 코드 (딕셔너리는 간단히는 정렬 안되므로)
    key_dict = uniq_tp_cliq.keys()
    key_list = list(key_dict)
    key_list.sort() 

    tcCombiningL = []
    for key in key_list:
        result = (key, uniq_tp_cliq[key])
        if key in uniq_tp_cliq.keys(): tcCombiningL.append(result)
            
    return tcCombiningL


def combiTC_select(tcCombining, pc):
    ThresHold = 0.3 # 김동욱,이수원(2017)에서 검증해서 제시한 값

    tcCombi_list = []
    for (tc00_00, combi_tc) in tcCombining:
        allcase_L=[] ; nega_L=[]
        for i in range(len(combi_tc)-1):
            source = combi_tc[i]
            targets = combi_tc[i+1:]

            ww_pmi = []
            nega = []
            for target in targets:
                pmi = pc.getPMI(source, target)
                result = (source+'_'+target, pmi)
                ww_pmi.append(result)
                if pmi == None: nega.append(result)
            allcase_L.append(ww_pmi)
            nega_L.append(nega)

        allcase = sum(allcase_L, []) ; nega = sum(nega_L, [])
        x = len(nega) ; y = len(allcase)
        distance = x/y
        result = (distance, tc00_00, combi_tc)
        if distance < ThresHold: tcCombi_list.append(result)
            
    return tcCombi_list


def best_tcCombi(tcCombi_list, pc):
    
    update_topic = {}
    for pmi,combi_n,tc_list in tcCombi_list:
        sum_pmi = 0
        n = 0
        for i in range(len(tc_list)):
            source = tc_list[i]
            targets = tc_list[i+1:]
            for target in targets:
                pmi = pc.getPMI(source, target)
                if pmi is not None: sum_pmi += pmi
                n += 1
        aver_pmi = sum_pmi/n
        update_topic[combi_n] = aver_pmi

    # 최종 TC 선정 (MAX.average(TMI))    
    for (key, values) in update_topic.items():
        if max(update_topic.values()) == values:
            max_tc_list = sum([tc_list for pmi,combi_n,tc_list in tcCombi_list if key == combi_n], [])
            return (key, max_tc_list)
