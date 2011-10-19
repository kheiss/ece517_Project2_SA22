<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Organisation - CSV Import Stylesheet

         2011-Jun-13 / Graeme Foster <graeme AT acm DOT org>

         - use for import to gis/location resource
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
         name....................gis_location.name
         level...................gis_location.level      (optional)
         parent..................gis_location.parent     (optional)
         lat.....................gis_location.lat
         lon.....................gis_location.lon
         elevation...............gis_location.elevation  (optional)

    *********************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- ********************************************************** -->
            <!-- Create each record -->
            <xsl:for-each select="table/row">
                <!-- Create the gis location -->
                <resource name="gis_location">
                    <data field="name"><xsl:value-of select="col[@field='name']"/></data>
                    <data field="lat"><xsl:value-of select="col[@field='lat']"/></data>
                    <data field="lon"><xsl:value-of select="col[@field='lon']"/></data>
                    <xsl:if test="col[@field='level']!=''">
                        <data field="level"><xsl:value-of select="col[@field='level']"/></data>
                    </xsl:if>
                    <xsl:if test="col[@field='parent']!=''">
                        <data field="parent"><xsl:value-of select="col[@field='parent']"/></data>
                    </xsl:if>
                    <xsl:if test="col[@field='elevation']!=''">
                        <data field="elevation"><xsl:value-of select="col[@field='elevation']"/></data>
                    </xsl:if>
                </resource>
            </xsl:for-each>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>
