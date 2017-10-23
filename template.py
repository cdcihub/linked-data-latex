from __future__ import print_function

import jinja2
import os
from jinja2 import Template
from jinja2 import Environment, BaseLoader
import argparse

import yaml
import re
from numpy import *
import glob

def get_latex_jinja_env():
    return jinja2.Environment(
            block_start_string = '\BLOCK{',
            block_end_string = '}',
            variable_start_string = '\VAR{',
            variable_end_string = '}',
            comment_start_string = '\#{',
            comment_end_string = '}',
            line_statement_prefix = '%%\LINE',
            line_comment_prefix = '%#',
            trim_blocks = True,
            autoescape = False,
            loader = jinja2.FileSystemLoader(os.path.abspath('.')),
        undefined=jinja2.StrictUndefined,
    )

def setup_custom_filters(latex_jinja_env):
    def format_preliminary(value):
        return "\\textcolor{red}{"+str(value)+"}"

    def format_wrt_t0(value):
        if value>0:
            return "~+~%.2lg"%abs(value)
        return "~-~%.2lg"%abs(value)

    def format_plusminus(value,ct=2):
        if log10(value['mean'])>3 or log10(value['mean'])<-2:
            value['scale_log10']=int(log10(value['mean']))
            if value['scale_log10']<0:
                value['scale_log10']-=1

            for v in 'mean','stat_err','stat_err_plus','stat_err_minus':
                if v in value:
                    value[v]=value[v]/10**value['scale_log10']

        if 'stat_err' in value:
            r = ("%%.%ilg~$\pm$~%%.%ilg"%(ct,ct))%(value['mean'],value['stat_err'])
        else:
            r = ("%%.%ilg\\small$^{+%%.%ilg}_{-%%.%ilg}$\\normalsize"%(ct,ct,ct))%(value['mean'],value['stat_err_plus'],value['stat_err_minus'])

        if 'scale_log10' in value:
            r+="$ \\times 10^{%i}$"%value['scale_log10']

        return r

    def format_latex_exp(value,ineq=False,mant_precision=2):
        if value is None or str(value).strip()=="" or (isinstance(value,str) and value.strip()==""):
            return "N/A"

        try:
            print("XX",value,"XX")
        except jinja2.exceptions.UndefinedError:
            return "N/A"

        try:
            value_exp=int(log10(value))
            if value_exp<0:
                value_exp-=1
            value_mant=value/10**value_exp
        except:
            raise

        if value_mant==10:
            value_mant=1
            value_exp+=1

        str_exp="10$^{%.2g}$"%(value_exp)
        str_mant=("%%.%ig"%mant_precision)%(value_mant)

        print("YYY::",value_mant,str_mant)

        if str_mant=="1":
            r=str_exp
        else:
            r=(str_mant+"$\\times$"+str_exp).strip()

        #r=("%.2g$\\times$10$^{%.2g}$"%(value_mant,value_exp)).strip()
        if ineq:
            r=r.replace("$","")

        print(r)

        return r

    def format_erange(value):
        if value['emax']<10000:
            return "%g~--~%g~keV"%(value['emin'],value['emax'])
        else:
            return "%g~keV~--~%g~MeV"%(value['emin'],value['emax']/1000)

    latex_jinja_env.filters['wrt_t0'] = format_wrt_t0
    latex_jinja_env.filters['latex_exp'] = format_latex_exp
    latex_jinja_env.filters['erange'] = format_erange
    latex_jinja_env.filters['plusminus'] = format_plusminus
    latex_jinja_env.filters['preliminary'] = format_preliminary

def load_data(rootdir="./data"):
    data={}
    for fn in glob.glob(rootdir+"/*.yaml"):
        key=fn.replace(rootdir+"/","").replace(".yaml","")
        data[key]=yaml.load(open(fn))
        print("rootdir",rootdir)
        print("loading data",fn,key)
    return data

def data_assertion(data):
    try:
        import assert_data
        assert_data.assert_draft_data(data)
    except ImportError:
        print("no data assertion: all data is meaningfull")

def extract_referenced_keys(draft_filename):
    reduced=[]
    for k in re.findall("\\VAR{(.*?)}", open(draft_filename).read()):
        if not k in reduced:
            print("found",k)
            reduced.append(k)
    return reduced



def render_definitions(latex_jinja_env,keys,data,output_filename):
    header = """
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% generated by template.py, please do not edit directly
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% boilerplate

\def\\addVAR#1#2{\expandafter\gdef\csname my@data@\detokenize{#1}\endcsname{#2}}
\def\VAR#1{%
  \ifcsname my@data@\detokenize{#1}\endcsname
    \csname my@data@\detokenize{#1}\expandafter\endcsname
  \else
    \expandafter\ERROR
  \\fi
}

% extracted definitions

"""

    output=open(output_filename,"w")
    output.write(header)
    for key in keys:
        rtemplate = latex_jinja_env.from_string("\VAR{"+key+"}")

        try:
            value=unicode(rtemplate.render(**data)).encode('utf8')
        except Exception as e:
            print("unable to render",key,e)
            value="XXX"

        output.write("\\addVAR{"+key+"}{"+value+"}\n")
    output.close()

def render_draft(latex_jinja_env,datam,input,output): # old way
    template = latex_jinja_env.get_template(input)
    header = """
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% generated by template.py, please do not edit directly
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
"""
    open(output,"w").write(unicode(header+template.render(**data)).encode('utf8'))


parser = argparse.ArgumentParser()
parser.add_argument("input",default="main.tex")
parser.add_argument("output",default="definitions.tex")
parser.add_argument("-d","--data",default="./data")
parser.add_argument("--draft",action='store_true',default=False)
args=parser.parse_args()


latex_jinja_env=get_latex_jinja_env()
setup_custom_filters(latex_jinja_env)

data=load_data(args.data)

if args.draft:
    render_draft(latex_jinja_env,
                       data,
                       args.input,
                       args.output)
else:
    render_definitions(latex_jinja_env,
                       extract_referenced_keys(args.input),
                       data,
                       output_filename=args.output)
