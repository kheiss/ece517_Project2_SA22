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
         Warehouse..............org_office
         Item group.............supply_item.name
         Item description.......supply_item.comments
         Catalogue number.......supply_catalog.name
         Tracking number (CTN)..
         Remark.................
         Outbound...............
         UM.....................supply_item.um
         Currency...............
         Price..................
         Stock..................
         Price..................
         Stock..................inv_inv_item.quantity
         Price..................
         Stock..................

    *********************************************************************** -->

    <xsl:output method="xml"/>
    <xsl:key name="warehouse" match="row" use="col[@field='Warehouse']"/>
    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Create the Warehouse -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('warehouse', col[@field='Warehouse'])[1])]">
                <xsl:variable name="warehouse" select="col[@field='Warehouse']/text()"/>
                <resource name="org_office">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$warehouse"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$warehouse"/></data>
                </resource>
                <xsl:for-each select="key('warehouse', col[@field='Warehouse'])">
                    <xsl:variable name="group" select="col[@field='Item group']/text()"/>
                    <resource name="supply_item">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$group"/>
                        </xsl:attribute>
                        <data field="name"><xsl:value-of select="$group"/></data>
                        <data field="um"><xsl:value-of select="col[@field='UM']/text()"/></data>
                    </resource>
                    <resource name="inv_inv_item">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$group"/>
                        </xsl:attribute>
                            <!-- Link to Supply Item -->
                            <reference field="item_id" resource="supply_item">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="$group"/>
                                </xsl:attribute>
                            </reference>
                            <!-- Link to Warehouse -->
                            <reference field="site_id" resource="org_office">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="$warehouse"/>
                                </xsl:attribute>
                            </reference>
                        <data field="quantity"><xsl:value-of select="col[@field='Stock']/text()"/></data>
                        <data field="comments"><xsl:value-of select="col[@field='Remark']/text()"/></data>
                    </resource>
                </xsl:for-each>
            </xsl:for-each>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>


