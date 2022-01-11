#!/usr/bin/python3

# gute_saetze.py

# Version 3.1.0

# Eingabe: Eine vrt-Datei, mit POS-Tags (UPenn Tagset) in der zweiten Spalte
#          Die VRT-Datei muss Satzauszeichnung durch <s>-Tags haben

# Ausgabe: Eine vrt-Datei, in der "schlechte" Saetze gestrichen sind
#
#          Eine Log-Datei mit statistischen Informationen

import sys
import re
import os
import langid
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("--lang", dest="lang", default="en")
ap.add_argument("--poscol", dest="pos_column", type=int, default=1)
ap.add_argument("infile")
ap.add_argument("outfile")
ap.add_argument("--log", dest="log", default="gute_saetze.log")
options = ap.parse_args()

infile = open(options.infile, "r")
outfile = open(options.outfile, "w")
logfile = open(options.log, "w")


# Parameter

min_token_count = 8 # Minimale Tokenzahl in einem guten Satz

# Intialisierungen

sentences_processed = 0
sentences_accepted  = 0
sentences_rejected  = 0
too_short_sentences = 0
verbless_sentences  = 0
foreign_sentences = 0
incomplete_sentences = 0
tokens_processed = 0
tokens_accepted = 0
tokens_rejected = 0
line_count = 0

lang_stats = {} # Empty dictionary
accept = 1
token_count = 0
has_verb = 0
in_sentence = 0
words = ""

buffered = 0 # Ist etwas im Puffer?
buffered_satz = ""
buffered_tokens = 0

# Hauptschleife

for zeile in infile:
  line_count +=1
  if "<text" in zeile:
    outfile.write(zeile)
  elif "</text" in zeile:
     if buffered:
       outfile.write(buffered_sentence)
       tokens_accepted += buffered_tokens
       sentences_accepted += 1
       buffered = 0
       buffered_sentence = ""
       buffered_tokens = 0
     outfile.write(zeile)
     in_sentence = 0
  elif "<s " in zeile or "<s>" in zeile:
    satz = zeile
    in_sentence = 1
    token_count = 0
    has_verb = 0
    accept = 1
    words = ""
  elif "</s>" in zeile:
    satz += zeile
    (language, x)  = langid.classify(words)
    if lang_stats.get(language) == None:
      lang_stats[language] = 1
    else:
       lang_stats[language] += 1
    in_sentence = 0
    if token_count < min_token_count:
      accept = 0
      too_short_sentences+=1
    if has_verb == 0:
      accept = 0
      verbless_sentences+=1
    if language != options.lang:
      accept = 0
      foreign_sentences += 1
    sentences_processed+=1
    if accept == 1:
      buffered = 1
      buffered_tokens = token_count
      buffered_sentence = satz
    else:
      sentences_rejected+=1 
      tokens_rejected += token_count
  elif zeile[0] == '<' and not in_sentence and not buffered:
    outfile.write(zeile)
  elif zeile[0] == '<' and not in_sentence and buffered:
    buffered_sentence += zeile
  elif zeile[0] == '<' and in_sentence:
    satz += zeile
  elif in_sentence:
    satz += zeile
    token_count+=1
    tokens_processed+=1
    w = zeile.strip().split("\t")[0]
    words += " "+w
    if token_count == 1:
      if re.search(r'[a-z]', w[0]):
        if buffered:
          sentences_rejected += 1
          tokens_rejected += buffered_tokens
          incomplete_sentences += 1
          buffered= 0
        accept = 0
        incomplete_sentences += 1 
      else:
        if buffered:
          outfile.write(buffered_sentence)
          sentences_accepted += 1
          tokens_accepted += buffered_tokens
          buffered = 0
    pos = zeile.strip().split("\t")[options.pos_column]
    if pos[0] == "V":
      has_verb = 1
  else: # This should not happen
    print ("This should not happen\n")
    print ("There is problably an error in "+sys.argv[1]+ " at line "+str(line_count)+"\n")
    exit(1)

# Schliesse Dateien

infile.close()
outfile.close()

# Schreibe Logdatei

logfile.write("Output from "+" ".join(sys.argv)+"\n\n")
logfile.write("Tokens processed:\t"+str(tokens_processed)+"\n")
percentage = tokens_accepted *100.0/tokens_processed
logfile.write("Tokens accepted:\t"+str(tokens_accepted)+"\t"+str(percentage)+"%\n")
percentage = tokens_rejected*100.0/tokens_processed
logfile.write("Tokens rejected:\t"+str(tokens_rejected)+"\t"+str(percentage)+"%\n\n")
logfile.write("Sentences processed:\t"+str(sentences_processed)+"\n")
percentage = sentences_accepted*100.0/sentences_processed
logfile.write("Sentences accepted:\t"+str(sentences_accepted)+"\t"+str(percentage)+"%\n")
percentage = sentences_rejected*100.0/sentences_processed
logfile.write("Sentences rejected:\t"+str(sentences_rejected)+"\t"+str(percentage)+"%\n")
logfile.write("Too short sentences:\t"+str(too_short_sentences)+"\n")
logfile.write("Verbless sentences:\t"+str(verbless_sentences)+"\n")
logfile.write("Foreign sentences:\t"+str(foreign_sentences)+"\n")
logfile.write("Incomplete sentences:\t"+str(incomplete_sentences)+"\n\n")
logfile.write("Language statistics (sentences)\n")
for l in sorted(lang_stats.keys()):
  logfile.write(l+"\t"+str(lang_stats[l])+"\n")
logfile.close()

exit(0)
