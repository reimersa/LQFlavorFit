#! /usr/bin/env python

from argparse import ArgumentParser
from printing_utils import *

import ROOT as rt
from tdrstyle_all import *
import os


rt.gROOT.SetBatch(1)



description = """Plotting variables from ntuples."""
parser = ArgumentParser(prog="plotter", description=description, epilog="Finished successfully!")
parser.add_argument('-i', "--infilenames", dest="infilenames", nargs='+', default=None, action='store', required=True,
                                           help="Name of the root file(s) to make plots from" )
parser.add_argument('-o', "--outfolder",   dest="outfolder", action='store', required=True,
                                           help="Name of the existing folder to store plots in.")
args = parser.parse_args()



def main():
    
    print(green('--> Starting to plot variables from ntuples.'))

    # Define the cross section of the signal (in pb) and the lumi of the data to compare to (full Run2 = 138/fb = 138E3/pb)
    cross_section_signal = 1.
    lumi = 138.E3

    # Load the input files and chain them together
    chain = rt.TChain('Events')
    nfiles_loaded = 0
    for infilename in args.infilenames:
        chain.Add(infilename)
        nfiles_loaded += 1
    ntotal = chain.GetEntries()
    eventweight = cross_section_signal * lumi / ntotal
    print(green('  --> Loaded %i files with %i events' % (nfiles_loaded, ntotal)))

    # Create and fill the histograms
    histholder = HistHolder()    
    histholder.book_default_hists()
    nsel = fill_histograms(histholder=histholder, chain=chain, eventweight=eventweight)
    print(green('  --> Selected %i events out of %i (%.1f%%)' % (nsel, ntotal, float(nsel)/float(ntotal)*100.)))

    # make plots, one for each histogram in the histfolder
    make_plots_from_histholder(histholder=histholder, outfoldername=args.outfolder, normalize_to_binwidth=False)

    print(green('--> Done with plotting variables from ntuples.'))






def make_plots_from_histholder(histholder, outfoldername, normalize_to_binwidth=False):
    # make plots, one for each histogram in the histfolder

    histnames = histholder.histdict.keys()
    for histname in histnames:
    
        # get corresponding histograms
        hist = histholder.histdict[histname]
        xmin = hist.GetXaxis().GetXmin()
        xmax = hist.GetXaxis().GetXmax()
        nameXaxis = hist.GetXaxis().GetTitle()
        nameYaxis = hist.GetYaxis().GetTitle()
        if normalize_to_binwidth: nameYaxis = 'Events / GeV'

        leg = tdrLeg(0.45,0.75,0.90,0.85, textSize=0.040)
        c = tdrCanvas(canvName='c', x_min=xmin, x_max=xmax, y_min=5E-1, y_max=hist.GetMaximum()*100, nameXaxis=nameXaxis, nameYaxis=nameYaxis, square=True, iPos=11)

        if normalize_to_binwidth: normalize_content_to_bin_width(histogram=hist)
        tdrDraw(hist, 'E HIST', mcolor=rt.kBlack, lcolor=rt.kBlack, marker=1, fstyle=0, lstyle=1)
        hist.SetLineWidth(2)
        leg.AddEntry(hist, 'Signal', 'L')
        leg.Draw()
        rt.gPad.SetLogy(1)

        c.SaveAs(os.path.join(outfoldername, histname+'.pdf'))
        del c



def fill_histograms(histholder, chain, eventweight):

    ievent = 0
    nselected = 0
    for event in chain:
        if ievent%10000 == 0: print(blue('    --> Filling event no. %i' % (ievent)))
        ievent += 1

        # Define event selection here
        keep_event = True
        
        if not keep_event: continue

        histholder.fill('tau1pt', event.tau1_pt, eventweight)
        histholder.fill('tau1charge', event.tau1_charge, eventweight)
        histholder.fill('n_tau', event.n_tau, eventweight)
        nselected += 1

    return nselected


class HistHolder():
    def __init__(self):
        self.histdict = {}

    def book_hist(self, name, *args):
        hist = rt.TH1F(name, *args)
        hist.SetDirectory(0)
        self.histdict[name] = hist

    def fill(self, name, *args):
        self.histdict[name].Fill(*args)

    def book_default_hists(self):
        self.book_hist('tau1pt', ';p_{T}^{gen. #tau 1} [GeV];Events / bin', 20, 0, 100)
        self.book_hist('tau1charge', ';charge (gen. #tau 1);Events / bin', 3, -1.5, 1.5)
        self.book_hist('n_tau', ';N_{#tau};Events / bin', 11, -0.5, 10.5)
        




def normalize_content_to_bin_width(histogram):

    # Normalize the content of each bin to the bin width
    for bin in range(1, histogram.GetNbinsX() + 1):
        content = histogram.GetBinContent(bin)
        error = histogram.GetBinError(bin)
        bin_width = histogram.GetBinWidth(bin)
        normalized_content = content / bin_width
        normalized_error = error / bin_width
        histogram.SetBinContent(bin, normalized_content)
        histogram.SetBinError(bin, normalized_error)

if __name__ == '__main__':
    main()
