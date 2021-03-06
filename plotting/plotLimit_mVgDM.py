from ROOT import TCanvas, TGraph, TGraphAsymmErrors, TLegend, TLatex, TFile, TTree, TH2D, TGraph2D
import ROOT as root
from array import array
from sys import argv,stdout,exit
from tdrStyle import *
import plotConfig
from glob import glob 
from collections import namedtuple
from math import log10

root.gROOT.SetBatch(1)

##Color palette
ncontours = 999;
root.TColor.InitializeColors();
#stops = [ 0.0000, 0.1250, 0.2500, 0.3750, 0.5000, 0.6250, 0.7500, 0.8750, 1.0000]
stops = [ 0.0000,       0.10,   0.200,     0.30,      0.4000,      0.50,    0.7500,    0.8750,    1.0000]
red   = [ 243./255., 243./255., 240./255., 240./255., 241./255., 239./255., 186./255., 151./255., 129./255.]
green = [   0./255.,  46./255.,  99./255., 149./255., 194./255., 220./255., 183./255., 166./255., 147./255.]
blue  = [   6./255.,   8./255.,  36./255.,  91./255., 169./255., 235./255., 246./255., 240./255., 233./255.]

stopsArray = array('d',stops)
redArray   = array('d',red)
greenArray = array('d',green)
blueArray  = array('d',blue)

root.TColor.CreateGradientColorTable(9, stopsArray, redArray, greenArray, blueArray, ncontours);
root.gStyle.SetNumberContours(ncontours);

root.gStyle.SetLabelSize(0.035,"X");
root.gStyle.SetLabelSize(0.035,"Y");
root.gStyle.SetLabelSize(0.035,"Z");


setTDRStyle()

XSECUNCERT=0.1
VERBOSE=False

drawLegend=True

iC=0
class Limit():
  def __init__(self,mMed,gDM,xsec=1):
    self.mMed=mMed
    self.gDM=gDM
    self.xsec=xsec
    self.cent=0
    self.up1=0
    self.up2=0
    self.down1=0
    self.down2=0
    self.obs=0

LimitPoint = namedtuple('LimitPoint',['mV','mChi','gdmv','gdma','gqv','gqa','limit'])
def parseLimitFiles2D(filepath):
  # returns a list of LimitPoints 
  limits = [] 
  filelist = glob(filepath)
  for f in filelist:
    ff = f.split('/')[-1].split('_')
    mMed = int(ff[1])
    mChi = int(ff[2].split('.')[0])
    ff = f.split('/')[-2].split('_')
    gdmv = float(ff[1].replace('p','.'))
    gdma = float(ff[3].replace('p','.'))
    gqv = float(ff[5].replace('p','.'))
    gqa = float(ff[7].replace('p','.'))
    l = Limit(mMed/1000.,max(gdmv,gdma))
    try:
      fin = TFile(f)
      t = fin.Get('limit')
      if not t:
        continue
      nL = t.GetEntries()
      limitNames = ['down2','down1','cent','up1','up2','obs']
      for iL in xrange(nL):
        t.GetEntry(iL)
        val = t.limit
        val = val / 0.68
        setattr(l,limitNames[iL],val)
      lp = LimitPoint(mMed/1000.,mChi,gdmv,gdma,gqv,gqa,l)
      limits.append(lp)
    except Exception as e:
      print e
      pass
    fin.Close()
  return limits

def makePlot2D(filepath,foutname,medcfg,gdmcfg,header):
  limits = parseLimitFiles2D(filepath)
  gs = {}
  for g in ['exp','expup','expdown','obs','obsup','obsdown']:
    gs[g] = TGraph2D()

  iP=0
  hgrid = TH2D('grid','grid',medcfg[0],medcfg[1],medcfg[2],gdmcfg[0],gdmcfg[1],gdmcfg[2])
  for p in limits:
    l = p.limit 
    if l.obs==0 or l.cent==0:
      print l.mMed,l.gDM
      continue
    hgrid.Fill(l.mMed,l.gDM)
    gs['exp'].SetPoint(iP,l.mMed,l.gDM,l.cent)
    gs['expup'].SetPoint(iP,l.mMed,l.gDM,l.up1)
    gs['expdown'].SetPoint(iP,l.mMed,l.gDM,l.down1)
    gs['obs'].SetPoint(iP,l.mMed,l.gDM,l.obs)
    gs['obsup'].SetPoint(iP,l.mMed,l.gDM,l.obs/(1-XSECUNCERT))
    gs['obsdown'].SetPoint(iP,l.mMed,l.gDM,l.obs/(1+XSECUNCERT))
    iP += 1

  hs = {}
  for h in ['exp','expup','expdown','obs','obsup','obsdown']:
    hs[h] = TH2D(h,h,medcfg[0],medcfg[1],medcfg[2],gdmcfg[0],gdmcfg[1],gdmcfg[2])
    # hs[h].SetStats(0); hs[h].SetTitle('')
    for iX in xrange(0,medcfg[0]):
      for iY in xrange(0,gdmcfg[0]):
        x = medcfg[1] + (medcfg[2]-medcfg[1])*iX/medcfg[0]
        y = gdmcfg[1] + (gdmcfg[2]-gdmcfg[1])*iY/gdmcfg[0]
        val = gs[h].Interpolate(x,y)
        if val == 0:
          val = 9999
        val = max(0.01,min(100,val))
        hs[h].SetBinContent(iX+1,iY+1,val)
        # if h=='obs':
        #   print iX+1,iY+1,x,y,gs[h].Interpolate(x,y)

  '''
  zaxis = hs['obs'].GetZaxis()
  nbins = zaxis.GetNbins()
  print nbins
  zaxis.SetBinLabel(1,'<10^{-2}')
  zaxis.SetBinLabel(nbins,'>10')
  '''

  hs['obsclone'] = hs['obs'].Clone() # clone it so we can draw with different settings
  for h in ['exp','expup','expdown','obsclone','obsup','obsdown']:
    hs[h].SetContour(2)
    hs[h].SetContourLevel(1,1)
    for iX in xrange(1,medcfg[0]+1):
      for iY in xrange(1,gdmcfg[0]+1):
        if hs[h].GetBinContent(iX,iY)<=0:
          hs[h].SetBinContent(iX,iY,100)

  global iC
  canvas = ROOT.TCanvas("canvas%i"%iC, '',  1000, 800)
  canvas.SetLogz()
  iC+=1

  frame = canvas.DrawFrame(medcfg[1],gdmcfg[1],medcfg[2],gdmcfg[2],"")

  frame.GetYaxis().CenterTitle();
  frame.GetYaxis().SetTitle(gdmcfg[3]);
  frame.GetXaxis().SetTitle("m_{V} [TeV]");
  frame.GetXaxis().SetTitleOffset(1.15);
  frame.GetYaxis().SetTitleOffset(1.15);

  frame.Draw()

  hs['obs'].SetMinimum(0.01)
  hs['obs'].SetMaximum(100.)

  hs['obs'].Draw("COLZ SAME")

  hs['obsclone'].SetLineStyle(1)
  hs['obsclone'].SetLineWidth(3)
  hs['obsclone'].SetLineColor(2)
  hs['obsclone'].Draw('CONT3 SAME')

  ctemp = root.TCanvas()
  hs['obsclone'].Draw('contlist')
  ctemp.Update()
  objs = root.gROOT.GetListOfSpecials().FindObject('contours')
  saveobs = (objs.At(0)).First()

  canvas.cd()

  hs['obsup'].SetLineStyle(2)
  hs['obsup'].SetLineWidth(1)
  hs['obsup'].SetLineColor(2)
  hs['obsup'].Draw('CONT3 SAME')

  hs['obsdown'].SetLineStyle(2)
  hs['obsdown'].SetLineWidth(1)
  hs['obsdown'].SetLineColor(2)
  hs['obsdown'].Draw('CONT3 SAME')

  hs['exp'].SetLineStyle(1)
  hs['exp'].SetLineWidth(3)
  hs['exp'].SetLineColor(1)
  hs['exp'].Draw('CONT3 SAME')

  hs['expup'].SetLineStyle(2)
  hs['expup'].SetLineWidth(1)
  hs['expup'].SetLineColor(1)
  hs['expup'].Draw('CONT3 SAME')

  hs['expdown'].SetLineStyle(2)
  hs['expdown'].SetLineWidth(1)
  hs['expdown'].SetLineColor(1)
  hs['expdown'].Draw('CONT3 SAME')

  if drawLegend:
    leg = root.TLegend(0.16,0.62,0.57,0.88);#,NULL,"brNDC");
    leg.SetHeader(header)
    leg.AddEntry(hs['exp'],"Median Expected  95% CL","L");
    leg.AddEntry(hs['expup'],"Exp. #pm 1 std. dev. (exp)","L");
    leg.AddEntry(hs['obsclone'],"Observed 95% CL","L");
    leg.AddEntry(hs['obsup'],"Obs. #pm 1 std. dev. (theory)","L");
    leg.SetFillColor(0); leg.SetBorderSize(0)
    leg.Draw("SAME");

#  hgrid.Draw('same')

  tex = root.TLatex();
  tex.SetNDC();
  tex.SetTextFont(42);
  tex.SetLineWidth(2);
  tex.SetTextSize(0.040);
  tex.Draw();
  tex.DrawLatex(0.6,0.94,"35.8 fb^{-1} (13 TeV)");
  tex2 = root.TLatex();
  tex2.SetNDC();
  tex2.SetTextFont(42);
  tex2.SetLineWidth(2);
  tex2.SetTextSize(0.04);
  tex2.SetTextAngle(270);
  tex2.DrawLatex(0.965,0.93,"Expected #sigma_{95% CL}/#sigma_{theory}");

  texCMS = root.TLatex(0.12,0.94,"#bf{CMS}");
  texCMS.SetNDC();
  texCMS.SetTextFont(42);
  texCMS.SetLineWidth(2);
  texCMS.SetTextSize(0.05); texCMS.Draw();

#  texPrelim = root.TLatex(0.2,0.94,"#it{Preliminary}");
#  texPrelim.SetNDC();
#  texPrelim.SetTextFont(42);
#  texPrelim.SetLineWidth(2);
#  texPrelim.SetTextSize(0.04); texPrelim.Draw();

  root.gPad.SetRightMargin(0.15);
  root.gPad.SetTopMargin(0.07);
  root.gPad.SetBottomMargin(0.15);
  root.gPad.RedrawAxis();
  root.gPad.Modified(); 
  root.gPad.Update();

  canvas.SaveAs(foutname+'.png')
  canvas.SaveAs(foutname+'.pdf')

  fsave = root.TFile(foutname+'.root','RECREATE')
  fsave.WriteTObject(hs['exp'],'hexp')
  fsave.WriteTObject(gs['exp'],'gexp')
  fsave.Close()
#  canvas.SaveAs(foutname+'.C')

plotsdir = plotConfig.plotDir

makePlot2D(plotConfig.scansDir+'vector/gdmv_*_gdma_0_gv_0p25_ga_0/higgsCombinefcnc_*_1.Asymptotic.mH120.root',
           plotsdir+'fcnc2d_obs_gdmv_mV',
           (100,0.3,2.2),
           (100,0.1,2,'g_{DM}^{V}'),
           'm_{#chi} = 1 GeV, g_{q}^{V} = 0.25 [FCNC]')

# makePlot2D(plotConfig.scansDir+'vector/gdmv_0_gdma_*_gv_0_ga_0p25/higgsCombinefcnc_*_1.Asymptotic.mH120.root',
#            plotsdir+'fcnc2d_obs_gdma_mV',
#            (100,300.,2200.),
#            (40,0.1,2,'g_{DM}^{A}'),
#            'm_{#chi} = 1 GeV, g_{q}^{A} = 0.25 [FCNC]')
