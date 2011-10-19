# -*- coding: utf-8 -*-

module = "climate"
if deployment_settings.has_module(module):
    local_import("ClimateDataPortal").define_models(env = Storage(globals()))
