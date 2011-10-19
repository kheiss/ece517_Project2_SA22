<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Inventory Warehouse - CSV Import Stylesheet

         1st May 2011 / Graeme Foster <graeme AT acm DOT org>

         - use for import to /inv/warehouse/create resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be inv/warehouse/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:
           
           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath
           
           You can add a third argument &ignore_errors

         CSV fields:
         Name............org_office.name
         Organisation....org_organisation.name
         Country.........org_office.l0
         State...........org_office.l1
         District........org_office.l2
         Lat.............gis_location.lat
         Lon.............gis_location.lon
         Address.........org_office.address
         Phone...........org_office.phone1
         Email...........org_office.email
         Comments........org_office.comments
         
        @todo:
            - make updateable (don't use temporary UIDs)

    *********************************************************************** -->

    <xsl:output method="xml"/>

    <xsl:include href="../../xml/countries.xsl"/>
    <xsl:key name="org" match="row" use="col[@field='Organisation']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Create the Organisation -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('org', col[@field='Organisation'])[1])]">
                <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
                <resource name="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrgName"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$OrgName"/></data>
                </resource>



                <!-- ****************************************************** -->
                <xsl:for-each select="key('org', col[@field='Organisation'])">
                    <xsl:variable name="Warehouse" select="col[@field='Name']/text()"/>
                    
                    <resource name="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:text>urn:iso:std:iso:3166:-1:code:</xsl:text>
                            <xsl:call-template name="iso2countryname">
                                <xsl:with-param name="country" select="col[@field='Country']"/>
                            </xsl:call-template>
                        </xsl:attribute>
                        <data field="name"><xsl:value-of select="col[@field='Country']/text()"/></data>
                        <data field="level"><xsl:text>L0</xsl:text></data>
                    </resource>

                    <xsl:if test="col[@field='State']!=''">
                        <resource name="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="col[@field='State']/text()"/>
                            </xsl:attribute>
                            <reference field="parent" resource="gis_location">
                                <xsl:attribute name="uuid">
                                    <xsl:text>urn:iso:std:iso:3166:-1:code:</xsl:text>
                                    <xsl:call-template name="iso2countryname">
                                        <xsl:with-param name="country" select="col[@field='Country']"/>
                                    </xsl:call-template>
                                </xsl:attribute>
                            </reference>
                            <data field="name"><xsl:value-of select="col[@field='State']/text()"/></data>
                            <data field="level"><xsl:text>L1</xsl:text></data>
                        </resource>
                    </xsl:if>
                    <xsl:if test="col[@field='District']!=''">
                        <resource name="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="col[@field='District']/text()"/>
                            </xsl:attribute>
                            <xsl:choose>
                                <xsl:when test="col[@field='State']!=''">
                                    <reference field="parent" resource="gis_location">
                                        <xsl:attribute name="tuid">
                                            <xsl:value-of select="col[@field='State']/text()"/>
                                        </xsl:attribute>
                                    </reference>
                                </xsl:when>
                                <xsl:otherwise>
                                    <reference field="parent" resource="gis_location">
                                        <xsl:attribute name="uuid">
                                            <xsl:text>urn:iso:std:iso:3166:-1:code:</xsl:text>
                                            <xsl:call-template name="iso2countryname">
                                                <xsl:with-param name="country" select="col[@field='Country']"/>
                                            </xsl:call-template>
                                        </xsl:attribute>
                                    </reference>
                                </xsl:otherwise>
                            </xsl:choose>
                            <data field="name"><xsl:value-of select="col[@field='District']/text()"/></data>
                            <data field="level"><xsl:text>L2</xsl:text></data>
                        </resource>
                    </xsl:if>
                    

     
                    <resource name="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$Warehouse"/>
                        </xsl:attribute>



                        <xsl:choose>
                            <xsl:when test="col[@field='District']!=''">
                                <reference field="parent" resource="gis_location">
                                    <xsl:attribute name="tuid">
                                        <xsl:value-of select="col[@field='District']/text()"/>
                                    </xsl:attribute>
                                </reference>
                            </xsl:when>
                            <xsl:when test="col[@field='State']!=''">
                                <reference field="parent" resource="gis_location">
                                    <xsl:attribute name="tuid">
                                        <xsl:value-of select="col[@field='State']/text()"/>
                                    </xsl:attribute>
                                </reference>
                            </xsl:when>
                            <xsl:otherwise>
                                <reference field="parent" resource="gis_location">
                                    <xsl:attribute name="uuid">
                                        <xsl:text>urn:iso:std:iso:3166:-1:code:</xsl:text>
                                        <xsl:call-template name="iso2countryname">
                                            <xsl:with-param name="country" select="col[@field='Country']"/>
                                        </xsl:call-template>
                                    </xsl:attribute>
                                </reference>
                            </xsl:otherwise>
                        </xsl:choose>
                        <data field="name"><xsl:value-of select="$Warehouse"/></data>
                        <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
                        <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
                        <data field="addr_street">
                            <xsl:value-of select="concat(
                                                    col[@field='Address'], ', ',
                                                    col[@field='District'], ', ',
                                                    col[@field='State'])"/>
                        </data>
                    </resource>
                    
                    <!-- The Warehouse resource which is an org_office record -->
                    <resource name="org_office">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$Warehouse"/>
                        </xsl:attribute>
                        <!-- Link to Location -->
                        <reference field="location_id" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$Warehouse"/>
                            </xsl:attribute>
                        </reference>
                        <!-- Link to Organisation -->
                        <reference field="organisation_id" resource="org_organisation">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$OrgName"/>
                            </xsl:attribute>
                        </reference>
                        <!-- Warehouse Data -->
                        <data field="name"><xsl:value-of select="$Warehouse"/></data>
                        <data field="L0"><xsl:value-of select="col[@field='Country']"/></data>
                        <data field="L1"><xsl:value-of select="col[@field='State']"/></data>
                        <data field="L2"><xsl:value-of select="col[@field='District']"/></data>
                        <data field="address"><xsl:value-of select="col[@field='Address']"/></data>
                        <data field="phone1"><xsl:value-of select="col[@field='Phone']"/></data>
                        <data field="email"><xsl:value-of select="col[@field='Email']"/></data>
                        <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
                    </resource>

                </xsl:for-each>

            </xsl:for-each>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>


