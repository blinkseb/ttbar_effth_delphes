#ifndef DEF_NN_PANALYSIS
#define DEF_NN_PANALYSIS

#include <vector>
#include "TString.h"
#include "TFile.h"
#include "TH1.h"
#include "THStack.h"
#include "TLegend.h"
#include "TMVA/Factory.h"
#include "TMVA/Reader.h"
#include "TCanvas.h"
#include "TGraph.h"
#include "TLine.h"

#include "defs.h"
#include "pproc.h"
#include "pconfig.h"

double min(double a, double b);

class PAnalysis{
  public:

  PAnalysis(PConfig *config);
  ~PAnalysis();

  void BuildDiscriminant(void);
  double EvalDiscriminant(PProc* proc = NULL);
  void DoHist(void);
  void DoPlot(void);
  void DoROC(void);
  void BkgEffWPPrecise(void);
  //void FiguresOfMerit(void);
  void WriteOutput(void);
  void WriteSplitRootFiles(void);
  void WriteResult(void);

  private:

  PConfig *myConfig;

  void AddProc(PProc* data);
  void OpenAllProc(void);
  void CloseAllProc(void);
  void FillStack(double integralSig);
  double Transform(double output);
  void DefineAndTrainFactory(void);
  void DefineSingleton(void);
  void InitDiscriminant(void);
  
  TFile* myOutputFile;
  THStack* myStack;

  int mySig;
  std::vector<unsigned int> myBkgs; // we may train against several backgrounds
  //double sRootB, sRootSB, sB;
  bool myEvalOnTrained;
  bool myDiscriminantIsDef;
  double myCut, myBkgEff, mySigEff;
  std::vector<float> myInputVars;

  TMVA::Factory* myFactory;
  TMVA::Reader* myReader;

  TString myName;
  TString myOutput;
  TString myMvaMethod;
  
  std::vector<PProc*> myProc;

  TCanvas* myCnvTraining;
  TCanvas* myCnvPlot;
  TLegend* myLegend;
  TCanvas* myCnvEff;
  TGraph* myROC;
  TLine* myLine;
  TLine* myCutLine;
};

bool mvaOutputSorter(std::vector<double> i, std::vector<double> j);

#endif
