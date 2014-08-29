#!python

import os, sys, string, time, BaseHTTPServer, getopt, re, subprocess, webbrowser
from operator import itemgetter

from utils import *
from propagate import Propagate

sys.path.append(INITIAL_UTILS)
from ruffus import *
from sort_contigs import *
_readlibs = []
_skipsteps = []
_cls = None
_lowmem = False
_checkForContaminant = False
_minContaminantTrustedLen = 0
_minPercentageInOne = 0.9751
_minPercentageWithAsmSize = 0.99
_maxAsm = 1.2
_settings = Settings()

def init(reads, skipsteps, cls, low, mintrust):
   global _readlibs
   global _skipsteps
   global _cls
   global _lowmem
   global _minContaminantTrustedLen
   global _checkForContaminant

   _readlibs = reads
   _skipsteps = skipsteps
   _cls = cls
   _lowmem = low

   if mintrust != None and mintrust != 0:
      _minContaminantTrustedLen = mintrust
      _checkForContaminant = True

@follows(Propagate)
@posttask(touch_file("%s/Logs/classify.ok"%(_settings.rundir)))
@files("%s/Propagate/out/%s.clusters"%(_settings.rundir,_settings.PREFIX),"%s/Logs/classify.ok"%(_settings.rundir))
def Classify(input,output):
#   if "Classify" in _skipsteps or _cls == None or "Assemble" in _skipsteps or "assemble" in _skipsteps:
   if "Classify" in _skipsteps:
       run_process(_settings, "touch %s/Propagate/out/%s.clusters"%(_settings.rundir, _settings.PREFIX), "Classify")
       run_process(_settings, "touch %s/Logs/classify.skip"%(_settings.rundir), "Classify")       
       return 0

   if not os.path.exists("%s/Classify/out/%s"%(_settings.rundir, _settings.taxa_level)):
       run_process(_settings, "mkdir %s/Classify/out/%s"%(_settings.rundir, _settings.taxa_level))

   if _cls.lower() != "metaphyler":
       #run_process(_settings, "python %s/python/sort_contigs.py %s/Propagate/in/%s.clusters %s/Propagate/out/%s.clusters %s/Propagate/out/%s.reads.clusters %s/tax_key.tab %s/FindORFS/out/%s.fna.bnk %s/FindORFS/out/%s.faa.bnk %s/FindORFS/out/%s.gene.map %s/Classify/out %s/Scaffold/in/%s.bnk %s"%(_settings.METAMOS_UTILS, _settings.rundir, _settings.PREFIX, _settings.rundir, _settings.PREFIX, _settings.rundir, _settings.PREFIX, _settings.DB_DIR, _settings.rundir, _settings.PREFIX, _settings.rundir, _settings.PREFIX, _settings.rundir, _settings.PREFIX, _settings.rundir, _settings.rundir, _settings.PREFIX,_settings.AMOS),"Classify")
       sort_contigs("%s/Propagate/in/%s.clusters"%(_settings.rundir,_settings.PREFIX),"%s/Propagate/out/%s.clusters"%(_settings.rundir,_settings.PREFIX),"%s/Propagate/out/%s.reads.clusters"%(_settings.rundir,_settings.PREFIX),"%s/tax_key.tab"%(_settings.DB_DIR),"%s/FindORFS/out/%s.fna.bnk"%(_settings.rundir,_settings.PREFIX),"%s/FindORFS/out/%s.faa.bnk"%(_settings.rundir,_settings.PREFIX),"%s/FindORFS/out/%s.gene.map"%(_settings.rundir,_settings.PREFIX),"%s/Classify/out/%s"%(_settings.rundir, _settings.taxa_level),"%s/Scaffold/in/%s.bnk"%(_settings.rundir,_settings.PREFIX),"%s"%(_settings.AMOS), _lowmem)
   else:
       #run_process(_settings, "python %s/python/sort_contigs.py %s/Propagate/in/%s.clusters %s/Propagate/out/%s.clusters %s/Propagate/out/%s.reads.clusters %s/class_key.tab %s/FindORFS/out/%s.fna.bnk %s/FindORFS/out/%s.faa.bnk %s/FindORFS/out/%s.gene.map %s/Classify/out %s/Scaffold/in/%s.bnk %s"%(_settings.METAMOS_UTILS, _settings.rundir, _settings.PREFIX, _settings.rundir, _settings.PREFIX, _settings.rundir, _settings.PREFIX, _settings.DB_DIR, _settings.rundir, _settings.PREFIX, _settings.rundir, _settings.PREFIX, _settings.rundir, _settings.PREFIX, _settings.rundir, _settings.rundir, _settings.PREFIX,_settings.AMOS),"Classify")
       sort_contigs("%s/Propagate/in/%s.clusters"%(_settings.rundir,_settings.PREFIX),"%s/Propagate/out/%s.clusters"%(_settings.rundir,_settings.PREFIX),"%s/Propagate/out/%s.reads.clusters"%(_settings.rundir,_settings.PREFIX),"%s/class_key.tab"%(_settings.DB_DIR),"%s/FindORFS/out/%s.fna.bnk"%(_settings.rundir,_settings.PREFIX),"%s/FindORFS/out/%s.faa.bnk"%(_settings.rundir,_settings.PREFIX),"%s/FindORFS/out/%s.gene.map"%(_settings.rundir,_settings.PREFIX),"%s/Classify/out/%s"%(_settings.rundir, _settings.taxa_level),"%s/Scaffold/in/%s.bnk"%(_settings.rundir,_settings.PREFIX),"%s"%(_settings.AMOS), _lowmem)

   # look for contaminant if requested
   if _checkForContaminant == True:
      run_process(_settings, "java -cp %s SizeFasta %s/Assemble/out/%s.asm.contig |awk '{if ($NF >= %s) { print $1} }' > %s/Classify/out/%s.ctg.iids"%(_settings.METAMOS_JAVA, _settings.rundir, _settings.PREFIX, _minContaminantTrustedLen, _settings.rundir, _settings.PREFIX), "Classify")

      run_process(_settings, "unlink %s/Classify/out/%s.read.iids"%(_settings.rundir, _settings.PREFIX), "Classify")
      for lib in _readlibs:
         run_process(_settings, "java -cp %s SizeFasta %s/Assemble/out/lib%d.unaligned.fasta |awk '{if ($NF >= %s) { print $1} }' >> %s/Classify/out/%s.read.iids"%(_settings.METAMOS_JAVA, _settings.rundir, lib.id, _minContaminantTrustedLen, _settings.rundir, _settings.PREFIX), "Classify")
         run_process(_settings, "java -cp %s SubFile %s/Classify/out/%s.ctg.iids %s/Assemble/out/%s.lib%dcontig.reads 1 >> %s/Classify/out/%s.read.iids"%(_settings.METAMOS_JAVA, _settings.rundir, _settings.PREFIX, _settings.rundir, _settings.PREFIX, lib.id, _settings.rundir, _settings.PREFIX), "Classify") 
      run_process(_settings, "java -cp %s SubFile %s/Classify/out/%s.read.iids %s/Propagate/out/%s.reads.clusters > %s/Classify/out/%s.read.contaminant.clusters"%(_settings.METAMOS_JAVA, _settings.rundir, _settings.PREFIX, _settings.rundir, _settings.PREFIX, _settings.rundir, _settings.PREFIX), "Classify")

      # now read and figure out percentage
      counts = {}
      total = 0
      filein = open("%s/Classify/out/%s.read.contaminant.clusters"%(_settings.rundir, _settings.PREFIX), 'r')
      for line in filein.xreadlines():
         line = line.replace("\n", "")
         read, annot = line.split()
         total += 1
         if annot not in counts:
            counts[annot] = 0
         counts[annot] += 1
      filein.close()

      run_process(_settings, "unlink %s/Classify/out/contaminant.true"%(_settings.rundir), "Classify")
      majority = 0
      classID = 1
      isContaminant = False
      for annot in counts:
         percentage = float(counts[annot]) / float(total)
         if percentage > majority:
            majority = percentage
            classID = annot
      
      if majority < _minPercentageInOne:
         isContaminant = True
      elif majority < _minPercentageWithAsmSize:
         isContaminant = True

         if os.path.exists("%s/Validate/out/%s.ref.fasta"%(_settings.rundir, _settings.PREFIX)):
            asmSize=getCommandOutput("java -cp %s SizeFasta %s/Assemble/out/%s.asm.contig |awk '{SUM+=$NF; print SUM}' |tail -n 1"%(_settings.METAMOS_JAVA, _settings.rundir, _settings.PREFIX), False)
            expectedSize=getCommandOutput("java -cp %s SizeFasta %s/Validate/out/%s.ref.fasta |awk '{SUM+=$NF; print SUM}' |tail -n 1"%(_settings.METAMOS_JAVA, _settings.rundir, _settings.PREFIX), False)
            if int(float(expectedSize) * _maxAsmSize) >= int(asmSize):
                isContaminant = False

      if isContaminant:
         name = getCommandOutput("cat %s/tax_key.tab |awk -F \"\\t\" '{if ($1 == %s) print $NF}'"%(_settings.DB_DIR, classID), False)
         contaminant = open("%s/Classify/out/contaminant.true"%(_settings.rundir), 'w')
         contaminant.write("%s\t%s\t%s\n"%(majority*100, name, _minContaminantTrustedLen))
         contaminant.close()
