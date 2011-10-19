<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         survey-Template - CSV Import Stylesheet

         2011-Jun-16 / Graeme Foster <graeme AT acm DOT org>

         - use for import to survey/series resource
         
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be survey/series/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:
           
           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath
           
           You can add a third argument &ignore_errors

         CSV fields:
         name..............survey_series
         description.......survey_series
         template..........survey_template
         organisation......org_organisation
         person_fname......pr_person
         person_lname......pr_person
         person_email......pr_person
         logo..............survey_series
         language..........survey_series
         start_date........survey_series
         end_date..........survey_series

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
                <!-- Lookup table Organisation -->
                <resource name="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="col[@field='organisation']"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="col[@field='organisation']"/></data>
                </resource>
                <!-- Lookup table person -->
                <xsl:variable name="person" select="col[@field='person_email']"/>
                <resource name="pr_person">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$person"/>
                    </xsl:attribute>
                    <data field="first_name"><xsl:value-of select="col[@field='person_fname']"/></data>
                    <data field="last_name"><xsl:value-of select="col[@field='person_lname']"/></data>
                    <!-- Contact Information -->
                    <resource name="pr_contact">
                        <data field="contact_method" value="1"/>
                        <data field="value"><xsl:value-of select="$person"/></data>
                    </resource>
                </resource>

                <!-- Create the Survey -->
                <resource name="survey_series">
                    <data field="name"><xsl:value-of select="col[@field='name']"/></data>
                    <data field="description"><xsl:value-of select="col[@field='description']"/></data>
                    <data field="logo"><xsl:value-of select="col[@field='logo']"/></data>
                    <data field="language"><xsl:value-of select="col[@field='language']"/></data>
                    <data field="start_date"><xsl:value-of select="col[@field='start_date']"/></data>
                    <data field="end_date"><xsl:value-of select="col[@field='end_date']"/></data>
                    <!-- Link to Template -->
                    <reference field="template_id" resource="survey_template">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="col[@field='template']"/>
                        </xsl:attribute>
                    </reference>
                    <!-- Link to Organisation -->
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="col[@field='organisation']"/>
                        </xsl:attribute>
                    </reference>
                    <!-- Create the User -->
                    <reference field="person_id" resource="pr_person">
                        <!-- Person record -->
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$person"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:for-each>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>
