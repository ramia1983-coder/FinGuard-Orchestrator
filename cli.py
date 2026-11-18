import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from finguard.service import process_file

p=argparse.ArgumentParser(description='Run FinGuard AML demo batch')
p.add_argument('csv',nargs='?',default='data/development_first_50000.csv')
p.add_argument('--limit',type=int,default=2000)
p.add_argument('--db',default='runtime/finguard.db')
a=p.parse_args()
print(process_file(a.csv,a.db,a.limit))
