#!/usr/bin/env python3

from aws_cdk import core

from covid_figs.covid_figs_stack import CovidFigsStack


app = core.App()
CovidFigsStack(app, "covid-figs", env={'region': 'us-west-2'})

app.synth()
