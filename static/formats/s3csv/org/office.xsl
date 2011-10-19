<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Organisation - CSV Import Stylesheet

         2011-Jun-13 / Graeme Foster <graeme AT acm DOT org>

         - use for import to org/office resource
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
         name....................org_office
         organisation............org_organisation
         type....................org_office
         country.................org_office
         building name...........org_office
         street address..........org_office & gis_location.addr_street
         post code...............org_office & gis_location.post_code
         state...................org_office & gis_location.addr_street
         town....................gis_location.addr_street
         lat.....................gis_location.lat
         lon.....................gis_location.lon
         phone1..................org_office
         phone2..................org_office
         email...................org_office
         fax.....................org_office
         comments................org_office

    *********************************************************************** -->
    <xsl:include href="../../../../static/formats/xml/countries.xsl"/>
    <xsl:template match="/">
        <s3xml>
            <!-- ********************************************************** -->
            <!-- Create each record -->
            <xsl:for-each select="table/row">
                <!-- Create the variables -->
                <xsl:variable name="OfficeName" select="col[@field='name']/text()"/>
                <xsl:variable name="l0" select="col[@field='country']/text()"/>
                <xsl:variable name="l1" select="col[@field='state']/text()"/>
                <xsl:variable name="l3" select="col[@field='town']/text()"/>

                <!-- Create the location records -->
                <resource name="gis_location">
                    <xsl:attribute name="uuid">
                        <xsl:text>urn:iso:std:iso:3166:-1:code:</xsl:text>
                        <xsl:call-template name="iso2countryname">
                            <xsl:with-param name="country" select="$l0"/>
                        </xsl:call-template>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$l0"/></data>
                    <data field="level"><xsl:text>L0</xsl:text></data>
                </resource>

                <xsl:if test="$l1!=''">
                    <resource name="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l1"/>
                        </xsl:attribute>
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:text>urn:iso:std:iso:3166:-1:code:</xsl:text>
                                <xsl:call-template name="iso2countryname">
                                    <xsl:with-param name="country" select="$l0"/>
                                </xsl:call-template>
                            </xsl:attribute>
                        </reference>
                        <data field="name"><xsl:value-of select="$l1"/></data>
                        <data field="level"><xsl:text>L1</xsl:text></data>
                    </resource>
                </xsl:if>




                <xsl:if test="$l3!=''">
                    <resource name="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l3"/>
                        </xsl:attribute>
                        <xsl:choose>
                            <xsl:when test="$l1!=''">
                                <reference field="parent" resource="gis_location">
                                    <xsl:attribute name="tuid">
                                        <xsl:value-of select="$l1"/>
                                    </xsl:attribute>
                                </reference>
                            </xsl:when>
                            <xsl:otherwise>
                                <reference field="parent" resource="gis_location">
                                    <xsl:attribute name="uuid">
                                        <xsl:text>urn:iso:std:iso:3166:-1:code:</xsl:text>
                                        <xsl:call-template name="iso2countryname">
                                            <xsl:with-param name="country" select="$l0"/>
                                        </xsl:call-template>
                                    </xsl:attribute>
                                </reference>
                            </xsl:otherwise>
                        </xsl:choose>
                        <data field="name"><xsl:value-of select="$l3"/></data>
                        <data field="level"><xsl:text>L3</xsl:text></data>
                    </resource>
                </xsl:if>
                    
                    
                    
                <resource name="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OfficeName"/>
                    </xsl:attribute>
                    <xsl:choose>
                        <xsl:when test="$l3!=''">
                            <reference field="parent" resource="gis_location">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="$l3"/>
                                </xsl:attribute>
                            </reference>
                        </xsl:when>
                        <xsl:when test="$l1!=''">
                            <reference field="parent" resource="gis_location">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="$l1"/>
                                </xsl:attribute>
                            </reference>
                        </xsl:when>
                        <xsl:otherwise>
                            <reference field="parent" resource="gis_location">
                                <xsl:attribute name="uuid">
                                    <xsl:text>urn:iso:std:iso:3166:-1:code:</xsl:text>
                                    <xsl:call-template name="iso2countryname">
                                        <xsl:with-param name="country" select="$l0"/>
                                    </xsl:call-template>
                                </xsl:attribute>
                            </reference>
                        </xsl:otherwise>
                    </xsl:choose>
                    <data field="name"><xsl:value-of select="$OfficeName"/></data>
                    <data field="lat"><xsl:value-of select="col[@field='lat']"/></data>
                    <data field="lon"><xsl:value-of select="col[@field='lon']"/></data>
                    <data field="addr_street">
                        <xsl:value-of select="concat(
                                                col[@field='street address'], ', ',
                                                col[@field='town'], ', ',
                                                col[@field='state'])"/>
                    </data>
                </resource>




                <!-- Lookup table org_organisation -->
                <resource name="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="col[@field='organisation']/text()"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="col[@field='organisation']"/></data>
                </resource>
                <!-- Create the Office -->
                <resource name="org_office">
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="col[@field='organisation']/text()"/>
                        </xsl:attribute>
                    </reference>
                    <!-- Lookup Location Reference -->
                    <reference field="location_id" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$OfficeName"/>
                        </xsl:attribute>
                    </reference>

                    <data field="name"><xsl:value-of select="$OfficeName"/></data>
                    <xsl:choose>
                        <xsl:when test="col[@field='type']='Headquarters'">
                            <data field="type">1</data>
                        </xsl:when>
                        <xsl:when test="col[@field='type']='Regional'">
                            <data field="type">2</data>
                        </xsl:when>
                        <xsl:when test="col[@field='type']='National'">
                            <data field="type">3</data>
                        </xsl:when>
                        <xsl:when test="col[@field='type']='Field'">
                            <data field="type">4</data>
                        </xsl:when>
                        <xsl:when test="col[@field='type']='Warehouse'">
                            <data field="type">5</data>
                        </xsl:when>
                    </xsl:choose>
                    <data field="l0">
                        <xsl:call-template name="iso2countryname">
                            <xsl:with-param name="country" select="col[@field='country']"/>
                        </xsl:call-template>
                    </data>
                    <data field="building_name"><xsl:value-of select="col[@field='building name']"/></data>
                    <data field="address"><xsl:value-of select="col[@field='street address']"/></data>
                    <data field="postcode"><xsl:value-of select="col[@field='post code']"/></data>
                    <data field="l1"><xsl:value-of select="col[@field='state']"/></data>
                    <data field="l3"><xsl:value-of select="col[@field='town']"/></data>
                    <data field="phone1"><xsl:value-of select="col[@field='phone1']"/></data>
                    <data field="phone2"><xsl:value-of select="col[@field='phone2']"/></data>
                    <data field="email"><xsl:value-of select="col[@field='email']"/></data>
                    <data field="fax"><xsl:value-of select="col[@field='fax']"/></data>
                    <data field="comments"><xsl:value-of select="col[@field='comments']"/></data>
                </resource>
            </xsl:for-each>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>
