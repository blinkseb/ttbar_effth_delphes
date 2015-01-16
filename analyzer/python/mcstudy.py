#!/nfs/soft/python/python-2.7.5-sl6_amd64_gcc44/bin/python2.7
# -*- coding: utf-8 -*-

# Author: Sebastien Wertz
#		  sebastien.wertz@uclouvain.be
# License: GPLv2
#!/usr/bin/python2.6

#### Preamble

import ROOT
import sys
import os
import numpy as np
import math

import driver
import fitter

######## CLASS MC STUDY CONFIG #####################################################

class PMCConfig:

	def __init__(self, cfgFileName):

		self.cfg = {}
		self.params = []

		with open(cfgFileName, "r") as cfgFile:
			
			# splitting the lines, skipping empty lines and comment lines (starting with a "#")
			cfgContent = cfgFile.read()
			lines = [ line for line in cfgContent.split("\n") if line is not "" ]
			lines = [ line for line in lines if line[0] is not "#" ]
			# splitting between the ":"
			lines = [ line.split("=") for line in lines ]
			for line in lines:
				# removing blank spaces before and after the "="
				line = [ driver.cleanBlanks(item) for item in line ]
				if line[0].find("param") >= 0:
						paramSet = {}
						paramList = line[1].split(";")
						for param in paramList:
							name = param.split(":")[0]
							name = driver.cleanBlanks(name)
							value = param.split(":")[1]
							value = driver.cleanBlanks(value)
							value = float(value)
							paramSet[name] = value
						self.params.append(paramSet)
				else:
					self.cfg[line[0]] = line[1]

######## MC STUDY MAIN #############################################################

def mcStudyMain(mcStudyFile):
	print "============================================="
	print "================= MISchief =================="
	print "============================================="
	print "== Reading configuration file {0}".format(mcStudyFile)
	myMCStudy = PMCConfig(mcStudyFile)
	print "== Reading analysis file {0}".format(myMCStudy.cfg["mvaCfg"])
	myConfig = driver.PConfig(myMCStudy.cfg["mvaCfg"])
	resultFile = myConfig.mvaCfg["outputdir"] + "/" + myConfig.mvaCfg["name"] + "_results.out"
	print "== Reading MVA MC tree result file {0}".format(resultFile)
	myMCResult = fitter.PResult()
	myMCResult.iniFromFile(resultFile)

	if myMCStudy.cfg["mode"] == "counting":
		outFile = ROOT.TFile(myMCStudy.cfg["outFile"], "RECREATE")
		for i,paramSet in enumerate(myMCStudy.params):
			print "== Doing a counting-experiment study using parameters:"
			print paramSet

			subDir = outFile.mkdir("params_"+str(i), "Param_Set_"+str(i))
			subDir.cd()

			histDict = {}
			corrList = {}
			#normHist = ROOT.TH1D("Norm_hist", "Norm (GeV^{-2})", 100, 0, 5)
			#dsquareHist = ROOT.TH1D("Norm_squared_hist", "Norm squared (GeV^{-4})", 100, 0, 5)
			weightedNormHist = ROOT.TH1D("Weighted_Norm_hist", "Weighted Norm", 100, 0, 10)
			resHist = ROOT.TH1D("Chi_Square_hist", "Chi Square", 100, 0, 50)

			nVar = 0
			for i,data in enumerate(myConfig.dataCfg):
				if data["signal"] == "1":
					nVar += 1
					myHist = ROOT.TH1D(data["name"]+"_hist",data["name"]+"/\Lambda^2 (GeV^{-2})", 100, -2, 2)
					histDict[data["name"]] = myHist
					myVarHist = ROOT.TH1D(data["name"]+"_StdDev_hist",data["name"]+" Std. Dev. (GeV^{-2})", 100, 0., 1.)
					histDict[data["name"]+"_StdDev"] = myVarHist
					
					for j,data2 in enumerate(myConfig.dataCfg):
						if data2["signal"] == "1" and j > i:
							corrList[[data["name"]+"/"+data2["name"]] = []

			#histDict["norm"] = normHist
			#histDict["dsquare"] = dsquareHist
			histDict["weightedNorm"] = weightedNormHist
			histDict["chisq"] = resHist

			mcStudyCounting(myConfig, myMCResult, paramSet, histDict, int(myMCStudy.cfg["pseudoNumber"]))

			corrHist = ROOT.TH2D("Correlations_hist","Correlations", nVar, nVar, 0, nVar, 0, nVar)
			
			for hist in histDict.values():
				if hist.Integral() != 0:
					hist.Scale(1./hist.Integral())
				hist.Write()

		outFile.Close()

	else:
		print "== Mode not valid"
		sys.exit(1)

######## MC STUDY SHAPE #############################################################
# Pseudo-experiments on the MC histograms for each branch

#def mcStudyShape():
	# get histograms for the processes for each branch


######## MC STUDY SHAPE #############################################################
# Pseudo-experiments on the predicted number of events for each branch

def mcStudyCounting(myConfig, myMCResult, params, histDict, pseudoNumber):
	print "== Doing MC Study: counting experiment on the tree."

	branchPDFs = {}
	branchMeans = {}
	branchVars = {}
	prodname = ""

	print "== Initializing multi-dimensional PDF."

	# generate PDFs: each branch is a Poisson with
	# mean = predicted number of events in that branch,
	# depending on the parameters chosen:
	allVarVec = myMCResult.branches[0][2].keys()
	varVec = []
	for proc in allVarVec:
		for data in myConfig.dataCfg:
			if data["name"] == proc:
				if data["signal"] == "1":
					varVec.append(proc)
				break

	for branch in myMCResult.branches:
		mean = ROOT.RooRealVar(branch[1] + "_events", "Predicted number of events in branch " + branch[1], 0.)
		for proc in branch[2].keys():
			for data in myConfig.dataCfg:
				if data["name"] == proc:
					if data["signal"] == "1":
						mean.setVal(branch[2][proc]*params[proc] + mean.getVal())
					else:
						mean.setVal(branch[2][proc] + mean.getVal())
		branchMeans[ branch[1] ] = mean

		var = ROOT.RooRealVar(branch[1] + "_var", "Variable for branch " + branch[1], 0, "GeV^-2")
		branchVars[ branch[1] ] = var

		pdf = ROOT.RooPoisson(branch[1] + "_pdf", "Poisson PDF for branch " + branch[1], var, mean)
		branchPDFs[ branch[1] ] = pdf

		prodname += "*" + branch[1] + "_pdf"
	
	# remove the "*" at the beginning of the product PDF name:
	prodname = prodname[1:]
	
	# generate "total" PDF (product of each branch's PDF)
	prodPDFList = ROOT.RooArgList()
	for pdf in branchPDFs.values():
		prodPDFList.add(pdf)
	prodPDF = ROOT.RooProdPdf("total_pdf", "Total PDF for all the branches", prodPDFList)

	print "== Generating pseudo-experiments."

	# generate pseudo-expts.
	prodArgSet = ROOT.RooArgSet()
	for var in branchVars.values():
		prodArgSet.add(var)
	dataSet = prodPDF.generate(prodArgSet, pseudoNumber)

	print "== Doing a weighted least-square fit on each pseudo-experiment result."
	
	nDoF = 0
	# translate dataset element in a PResult and call fit on each pseudo-experiment
	for i in range(pseudoNumber):
		rdsRow = dataSet.get(i)
		myDataResult = fitter.PResult()
		myDataResult.iniFromRDS(myMCResult, rdsRow)
		result,chisq,nDoF,var,corr = fitter.weightedLstSqCountingFit(myConfig, myMCResult, myDataResult)
		dsquare = 0.
		weighteddsquare = 0.
		for proc in result.keys():
			dsquare += result[proc]**2
			weighteddsquare += result[proc]**2/var[proc]
		for proc in varVec:
			histDict[proc].Fill(result[proc])
			histDict[proc+"_StdDev"].Fill(math.sqrt(var[proc]))
		#histDict["norm"].Fill(math.sqrt(dsquare))
		#histDict["dsquare"].Fill(dsquare)
		histDict["weightedNorm"].Fill(math.sqrt(weighteddsquare))
		histDict["chisq"].Fill(chisq)
	histDict["chisq"].SetTitle(histDict["chisq"].GetTitle() + " (" + str(nDoF) + " D.o.F.)")

	print "== Done."

######## MAIN #############################################################

if __name__ == "__main__":
	mcStudyMain(sys.argv[1])
