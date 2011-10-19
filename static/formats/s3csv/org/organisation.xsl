<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Organisation - CSV Import Stylesheet

         2011-Jun-13 / Graeme Foster <graeme AT acm DOT org>

         - use for import to org/organisation resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be org/organisation/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:
           
           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath
           
           You can add a third argument &ignore_errors
         CSV fields:
         name....................org_organisation
         acronym.................org_organisation
         type....................org_organisation
         sector..................org_sector
         country.................org_organisation
         website.................org_organisation
         twitter.................org_organisation
         donation_phone..........org_organisation
         comments................org_organisation

    *********************************************************************** -->
    <xsl:include href="../../../../static/formats/xml/countries.xsl"/>
    <xsl:template match="/">
        <s3xml>
            <!-- ********************************************************** -->
            <!-- Create each record -->
            <xsl:for-each select="table/row">
                <!-- Lookup table org_sector -->
                <resource name="org_sector">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="col[@field='sector']/text()"/>
                    </xsl:attribute>
                    <data field="abrv"><xsl:value-of select="col[@field='sector']"/></data>
                </resource>
                <!-- Create the Organisation -->
                <resource name="org_organisation">
                    <data field="name"><xsl:value-of select="col[@field='name']"/></data>
                    <data field="acronym"><xsl:value-of select="col[@field='acronym']"/></data>
                    <xsl:choose>
                        <xsl:when test="col[@field='type']='Government'">
                            <data field="type">1</data>
                        </xsl:when>
                        <xsl:when test="col[@field='type']='Embassy'">
                            <data field="type">2</data>
                        </xsl:when>
                        <xsl:when test="col[@field='type']='International NGO'">
                            <data field="type">3</data>
                        </xsl:when>
                        <xsl:when test="col[@field='type']='Donor'">
                            <data field="type">4</data>
                        </xsl:when>
                        <xsl:when test="col[@field='type']='National NGO'">
                            <data field="type">6</data>
                        </xsl:when>
                        <xsl:when test="col[@field='type']='UN'">
                            <data field="type">7</data>
                        </xsl:when>
                        <xsl:when test="col[@field='type']='International Organization'">
                            <data field="type">8</data>
                        </xsl:when>
                        <xsl:when test="col[@field='type']='Military'">
                            <data field="type">9</data>
                        </xsl:when>
                        <xsl:when test="col[@field='type']='Private'">
                            <data field="type">10</data>
                        </xsl:when>
                        <xsl:when test="col[@field='type']='Intergovernmental Organization'">
                            <data field="type">11</data>
                        </xsl:when>
                        <xsl:when test="col[@field='type']='Institution'">
                            <data field="type">12</data>
                        </xsl:when>
                        <xsl:when test="col[@field='type']='Red Cross / Red Crescent'">
                            <data field="type">13</data>
                        </xsl:when>
                        <xsl:otherwise>
                            <data field="type">0</data>
                        </xsl:otherwise>
                    </xsl:choose>
                    <reference field="sector_id" resource="org_sector">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('[&quot;', col[@field='sector']/text(), '&quot;]')"/>
                        </xsl:attribute>
                    </reference>
                    <data field="country">
                        <xsl:call-template name="iso2countryname">
                            <xsl:with-param name="country" select="col[@field='country']"/>
                        </xsl:call-template>
                    </data>
                    <data field="website"><xsl:value-of select="col[@field='website']"/></data>
                    <data field="twitter"><xsl:value-of select="col[@field='twitter']"/></data>
                    <data field="donation_phone"><xsl:value-of select="col[@field='donation_phone']"/></data>
                    <data field="comments"><xsl:value-of select="col[@field='comments']"/></data>
                </resource>
            </xsl:for-each>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>
