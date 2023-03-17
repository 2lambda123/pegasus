#!/usr/bin/env python3

"""
Pegasus utility for reporting successful and failed jobs

Usage: pegasus-analyzer [options]

"""

##
#  Copyright 2007-2012 University Of Southern California
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing,
#  software distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
##

# Revision : $Revision: 2023 $


import os
import sys
import json
import click
import logging
import traceback
from Pegasus import analyzer

root_logger = logging.getLogger()

class HelpCmd(click.Command):
    def format_usage(self, ctx, formatter):
        click.echo(f"Usage: pegasus-analyzer [options] workflow_directory")


@click.command(cls=HelpCmd, options_metavar="<options>")
@click.pass_context
@click.option(
    "--verbose",
    "-v",
    "vb",
    count=True,
    help="Increase verbosity, repeatable",
)
@click.option(
    "-i",
    "-d",
    "--input-dir",
    "input_dir",
    required=False,
    metavar="INPUT_DIR",
    type=click.Path(file_okay=False, dir_okay=True, readable=True, exists=True),
    help="Input directory where the jobstate.log file is located, default is the current directory",
)
@click.option(
    "--dag",
    "dag_filename",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, exists=True),
    required=False,
    metavar="DAG_FILENAME",
    help="Full path to the dag file to use -- this option overrides the -d option",
)
@click.option(
    "-f",
    "--files",
    "use_files",
    is_flag=True,
    default=False,
    help="Disables the database mode and forces the use of workflow directory files",
)
@click.option(
    "-m",
    "-t",
    "--monitord",
    "run_monitord",
    is_flag=True,
    help="Run pegasus-monitord before analyzing the output",
)
@click.option(
    "-o",
    "--output-dir",
    "output_dir",
    required=False,
    metavar="OUTPUT_DIR",
    type=click.Path(file_okay=False, dir_okay=True, readable=True, exists=True),
    help="Provides an output directory for all monitord log files",
)
@click.option(
    "--top-dir",
    "top_dir",
    required=False,
    metavar="TOP_DIR",
    type=click.Path(file_okay=False, dir_okay=True, readable=True, exists=True),
    help="Provides the location of the top-level workflow directory, needed to analyze sub-workflows",
)
@click.option(
    "-c",
    "--conf",
    "config_properties",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, exists=True),
    required=False,
    metavar="CONFIG_PROPERTIES_FILE",
    help="Specifies the properties file to use. This overrides all other property files.",
)
@click.option(
    "-q",
    "--quiet",
    "quiet_mode",
    is_flag=True,
    help="Output out/err filenames instead of their contents",
)
@click.option(
    "-r",
    "--recurse",
    "recurse_mode",
    is_flag=True,
    help="Automatically recurse into sub workflows in case of failure",
)
@click.option(
    "-I",
    "--indent",
    "indent_length",
    type=int,
    metavar="INDENT_LENGTH",
    default=0,
    help="Dictates the number of white spaces to use when indenting the output",
)
@click.option(
    "-p",
    "--print",
    "print_options",
    type=str,
    metavar="PRINT_OPTIONS",
    help="Specifies print options from pre, invocation or all",
)
@click.option(
    "-s",
    "--strict",
    "strict_mode",
    is_flag=True,
    help="gets a job's out and err files from the submit file",
)
@click.option(
    "-S",
    "--summary",
    "summary_mode",
    is_flag=True,
    help="Just print the summary and exit",
)
@click.option(
    "-T",
    "--traverse-all",
    "traverse_all",
    is_flag=True,
    help="Traverse through all sub workflows for this workflow in the database",
)
@click.option(
    "--debug-job",
    "debug_job",
    type=str,
    metavar="DEBUG_JOB",
    help="Specifies a job to debug (can be either the job base name or the submit file name) -- this option enables debugging a single pegasus lite job",
)
@click.option(
    "--local-executable",
    "debug_job_local_executable",
    type=str,
    metavar="DEBUG_JOB_LOCAL_EXECUTABLE",
    help="The path to the local user application that pegasus-lite job refers to.",
)
@click.option(
    "--debug-dir",
    "debug_dir",
    required=False,
    metavar="DEBUG_DIR",
    type=click.Path(file_okay=False, dir_okay=True, readable=True, exists=True),
    help="Specifies the directory to use as debug directory (default is to create a random directory in /tmp)",
)
@click.option(
    "--type",
    "workflow_type",
    type=str,
    metavar="WORKFLOW_TYPE",
    help="Specifies what type of workflow we are debugging (available types: condor)",
)
@click.option(
    "-j",
    "--json",
    "json_mode",
    is_flag=True,
    help="Returns job info in a structured format",
)
@click.argument(
    "submit-dir",
    required=False,
    type=click.Path(file_okay=False, dir_okay=True, readable=True, exists=True)
)
def pegasus_analyzer(ctx,
                     vb,
                     input_dir,
                     dag_filename,
                     use_files,
                     run_monitord,
                     output_dir,
                     top_dir,
                     config_properties,
                     quiet_mode,
                     recurse_mode,
                     indent_length,
                     print_options,
                     strict_mode,
                     summary_mode,
                     traverse_all,
                     debug_job,
                     debug_job_local_executable,
                     debug_dir,
                     workflow_type,
                     submit_dir,
                     json_mode):

    
    if vb == 0:
        lvl = logging.WARN
    elif vb == 1:
        lvl = logging.INFO
    else:
        lvl = logging.DEBUG
    root_logger.setLevel(lvl)

    # Initializes user options data class used to run analyzer
    options = analyzer.Options(
    debug_dir = debug_dir,
    debug_job_local_executable = debug_job_local_executable,
    workflow_type = workflow_type,
    run_monitord = run_monitord,
    strict_mode = strict_mode,
    summary_mode = summary_mode,
    quiet_mode = quiet_mode,
    recurse_mode = recurse_mode,
    traverse_all = traverse_all,
    json_mode = json_mode,
    indent_length = indent_length
    )

    if print_options is not None:
        my_options = print_options.split(",")
        if "pre" in my_options or "all" in my_options:
            options.print_pre_script = True
        if "invocation" in my_options or "all" in my_options:
            options.print_invocation = True
            
    if top_dir is not None:
        options.top_dir = os.path.abspath(top_dir)
        
    if debug_job is not None:
        options.debug_job = debug_job
        # Enables the debugging mode
        options.debug_mode = True

    for num in range(0, options.indent_length):
        analyzer.indent += "\t"
    
    if dag_filename :
        options.input_dir = os.path.abspath(os.path.split(dag_filename)[0])
        # Assume current directory if input dir is empty
        if input_dir == None:
            options.input_dir = os.getcwd()
    else:
        # Select directory where jobstate.log is located
        if input_dir :
            options.input_dir = os.path.abspath(input_dir)
        elif submit_dir :
            options.input_dir = submit_dir
        else:
            options.input_dir = os.getcwd()

    if options.debug_mode == 1:
        # Enter debug mode if job name given
        try:
            debug = analyzer.DebugWF(options)
            debug.debug_workflow()
            ctx.exit(0)
        except:
            ctx.exit(1)

    # sanity check
    if recurse_mode and traverse_all:
        analyzer.logger.error(
            "Options --recurse and --traverse-all are mutually exclusive. Please specify only one of these options"
        )
        ctx.exit(1)
    
    # Run the analyzer
    try:
        # Run via the files option (using jobstate.log, dag file etc)
        if use_files:
            analyze = analyzer.AnalyzeFiles(options)
            if json_mode:
                output = analyze.analyze_files()
                print(json.dumps(output.as_dict(), indent=2))
            else:
                analyze.analyze_files()
    
        # Run via quering the stampede database        
        else:
            analyze = analyzer.AnalyzeDB(options)
            if json_mode:
                output = analyze.analyze_db(config_properties)
                print(json.dumps(output.as_dict(), indent=2))
            else:
                analyze.analyze_db(config_properties)
    except analyzer.AnalyzerError as err:
            analyzer.logger.error(err)
            ctx.exit(1)
    except analyzer.WorkflowFailureError as err:
            analyzer.logger.error(err)
            ctx.exit(2)
    except Exception:
            analyzer.logger.error(traceback.format_exc())
            ctx.exit(1)
    
    # Done!
    if not json_mode:
        print("Done".center(80, "*"))
        print()
        print("%s: end of status report" % (analyzer.prog_base))
        print()
    

if __name__ == "__main__":
    pegasus_analyzer()