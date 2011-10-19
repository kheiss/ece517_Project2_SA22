<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         survey-section - CSV Import Stylesheet

         2011-Jun-16 / Graeme Foster <graeme AT acm DOT org>

         - use for import to survey/series resource
         
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be survey/section/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:
           
           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath
           
           You can add a third argument &ignore_errors

         CSV fields:
         name..............survey_series
         description.......survey_series
         position..........survey_series
         template..........survey_template

    *********************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- ********************************************************** -->
            <!-- Create each record -->
            <xsl:for-each select="table/row">
                <!-- Lookup table survey_template -->
                <resource name="survey_template">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="col[@field='template']"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="col[@field='template']"/></data>
                </resource>
                <!-- Create the Survey -->
                <resource name="survey_section">
                    <data field="name"><xsl:value-of select="col[@field='name']"/></data>
                    <data field="description"><xsl:value-of select="col[@field='description']"/></data>
                    <data field="position"><xsl:value-of select="col[@field='position']"/></data>
                    <!-- Link to Template -->
                    <reference field="template_id" resource="survey_template">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="col[@field='template']"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:for-each>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>
