#! /usr/bin/env python

from argparse import ArgumentParser

import ROOT as rt
from DataFormats.FWLite import Events, Handle

from tqdm import tqdm
from array import array
rt.gROOT.SetBatch(1)



description = """Converting GENSIM files to flat ROOT files for analysis."""
parser = ArgumentParser(prog="converter",description=description,epilog="Finished successfully!")
parser.add_argument('-i', "--infilenames", dest="infilenames", default=None, action='store', nargs='+',
                                           help="Name of the GENSIM file(s)" )
parser.add_argument('-o', "--outfilename", dest="outfilename", default=None, action='store',
                                           help="Name of the output ROOT file" )
args = parser.parse_args()



def main():
    
    print '--> Starting GENSIM -> ROOT conversion.'
    
    # Load input files
    existing_files = get_existing_files_from_list(infilenames=args.infilenames)
    events = Events(existing_files)
    print '  --> Loaded %i files.' % (len(existing_files))

    # Prepare output file
    file_root = rt.TFile(args.outfilename, 'RECREATE')
    outtree = rt.TTree('Events', 'Some variables converted from GENSIM to flat ROOT format')
    
    # Define variables to fill into the output tree
    tau1_pt     = array('f', [ 0. ])
    tau1_eta    = array('f', [ 0. ])
    tau1_phi    = array('f', [ 0. ])
    tau1_e      = array('f', [ 0. ])
    tau1_charge = array('f', [ 0. ])
    n_tau       = array('f', [ 0. ])

    # Define variables of the output tree
    outtree.Branch('tau1_pt',     tau1_pt,     'tau1_pt/F')
    outtree.Branch('tau1_eta',    tau1_eta,    'tau1_eta/F')
    outtree.Branch('tau1_phi',    tau1_phi,    'tau1_phi/F')
    outtree.Branch('tau1_e',      tau1_e,      'tau1_e/F')
    outtree.Branch('tau1_charge', tau1_charge, 'tau1_charge/F')
    outtree.Branch('n_tau',       n_tau,       'n_tau/F')
    handle_gps, label_gps = Handle('std::vector<reco::GenParticle>'), 'genParticles'

    # Start the event loop!
    ie = 0
    for e in events:
        if ie%1000 == 0: print '  --> New event no. %i' % (ie)
        ie += 1

        e.getByLabel(label_gps,handle_gps)
        gps = handle_gps.product()

        # Access the gen-particles 
        gps_hard       = [p for p in gps if p.isHardProcess()]
        tau_hard       = [p for p in gps_hard if abs(p.pdgId()) == 15]
        tau_hard_final = [p for p in tau_hard if isFinal(p)]
        tau_hard_final.sort(key=lambda p: p.pt(), reverse=True)
        # mu_final = [p for p in gps if isFinal(p) and abs(p.pdgId()) == 13 and p.status() == 1]
        # mu_final.sort(key=lambda p: p.pt(), reverse=True)
    
        # Define a 4-momentum vector (for later use)
        tau1 = rt.TLorentzVector()

        # Fill the 4-momentum vector and the individual branches of the tree
        if len(tau_hard_final) > 0: 
            tau1.SetPxPyPzE(tau_hard_final[0].p4().Px(), tau_hard_final[0].p4().Py(), tau_hard_final[0].p4().Pz(), tau_hard_final[0].p4().E())
          tau1_pt[0]   = tau1.Pt()
          tau1_eta[0]  = tau1.Eta()
          tau1_phi[0]  = tau1.Phi()
          tau1_e[0]    = tau1.E()
          tau1_charge[0]= -1. if tau_hard_final[0].pdgId() > 0 else +1.

        n_tau[0] = len(tau_hard_final)

        # Finally, store all variables in the tree for this event, on to the next one.
        outtree.Fill()
    

    # Write the complete output tree into the output file and close it
    file_root.cd()
    outtree.Write()
    file_root.Close()

    print '--> Output written to: %s' % (args.outfilename)
    print '--> Done with GENSIM -> ROOT conversion.'




### HELPER FUNCTIONS
### ================

def get_existing_files_from_list(infilenames):
    existing_files = []
        for idx in range(len(infilenames)):
        try:
            f = rt.TFile.Open(infilenames[idx], 'READ')
            f.Close()
            existing_files.append(infilenames[idx])
        except:
            print '  --> In the given list of input files, this one does not exist: %s' % (infilenames[idx])
    return existing_files

def isFinal(p):
    # check if one daughter is final and has same PID, then it's not final
    return not (p.numberOfDaughters()==1 and p.daughter(0).pdgId()==p.pdgId())

def printParticle(p):
    string = "Particle with pdgId %9d: status=%2d, pt=%7.2f, eta=%5.2f, phi=%5.2f, final=%5s"%(p.pdgId(),p.status(),p.pt(),p.eta(),p.phi(),isFinal(p))
    if p.numberOfMothers()>=2:
        string += ", mothers %s, %s"%(p.mother(0).pdgId(),p.mother(1).pdgId())
    elif p.numberOfMothers()==1:
        string += ", mother %s"%(p.mother(0).pdgId())
    if p.numberOfDaughters()>=2:
        string += ", daughters %s, %s"%(p.daughter(0).pdgId(),p.daughter(1).pdgId())
    elif p.numberOfDaughters()==1:
        string += ", daughter %s"%(p.daughter(0).pdgId())
    print string

def printDecayChain(mothers):
    for m in mothers:
        daus   = []
        gdaus  = []
        ggdaus = []
        gggdaus = []
        print '='*10 + ' New mother:'
        printParticle(m)
        for d_idx in range(m.numberOfDaughters()):
            d = m.daughter(d_idx)
            daus.append(d)
            # printParticle(d)
        print '-'*10 + ' Daughters:'
        for d in daus:
            printParticle(d)
            for g_idx in range(d.numberOfDaughters()):
                g = d.daughter(g_idx)
                gdaus.append(g)
        print '-'*10 + ' Grand daughters:'
        for g in gdaus:
            printParticle(g)
            for gg_idx in range(g.numberOfDaughters()):
                gg = g.daughter(gg_idx)
                ggdaus.append(gg)
        print '-'*10 + ' Great grand daughters:'
        for gg in ggdaus:
            printParticle(gg)
  
    for g_idx in range(d.numberOfDaughters()):
        g = d.daughter(g_idx)
        printParticle(g)
        for gg_idx in range(d.numberOfDaughters()):
            gg = d.daughter(gg_idx)
            printParticle(gg)

def getFinalDaughter(p):
    thisp = p
    while not isFinal(thisp):
        thisp = thisp.daughter(0)
    return thisp


if __name__ == '__main__':
    main()
