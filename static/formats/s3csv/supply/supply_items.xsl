<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
    
    <!-- **********************************************************************
         Item Categories - CSV Import Stylesheet

         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be supply/catalog_item/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:
           
           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath
           
           You can add a third argument &ignore_errors
         CSV fields:
         Catalogue.......................supply_catalog.name
         Cat Code........................supply_item_category.code
         Category........................supply_item_category.name
         Name............................supply_item.name
         Unit of Measure.................supply_item.um
         Notes...........................supply_item.comments
         
         supply_catalog_item uses references to supply_catalog,
                                                supply_item_category,
                                                supply_item
            
    *********************************************************************** -->

    <xsl:output method="xml"/>

    <xsl:template match="/">
        <s3xml>
            <!-- Create each record -->
            <xsl:for-each select="table/row">
    
                <!-- Supply Catalogue -->
                <xsl:variable name="CatalogName"><xsl:value-of select="col[@field='Catalogue']"/></xsl:variable>
                <resource name="supply_catalog">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$CatalogName"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$CatalogName"/></data>
                </resource>

                <!-- Supply Item Category -->
                <resource name="supply_item_category">
	                <xsl:attribute name="tuid">
	                    <xsl:value-of select="col[@field='Category']"/>
	                </xsl:attribute>
                    <reference field="catalog_id" resource="supply_catalog">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$CatalogName"/>
                        </xsl:attribute>
                    </reference>
	                <data field="code"><xsl:value-of select="col[@field='Cat Code']"/></data>
	                <data field="name"><xsl:value-of select="col[@field='Category']"/></data>
	            </resource>
	            
                <!-- Supply Item -->
                <resource name="supply_item">
	                <xsl:attribute name="tuid">
	                    <xsl:value-of select="col[@field='Name']"/>
	                </xsl:attribute>
                    <reference field="item_category_id" resource="supply_item_category">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="col[@field='Category']"/>
                        </xsl:attribute>
                    </reference>
	                <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
	                <data field="um"><xsl:value-of select="col[@field='Unit of Measure']"/></data>
	                <data field="comments"><xsl:value-of select="col[@field='Notes']"/></data>
	            </resource>
	            
                <!-- Supply Catalogue Item -->
                <resource name="supply_catalog_item">
                    <reference field="catalog_id" resource="supply_catalog">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$CatalogName"/>
                        </xsl:attribute>
                    </reference>
                    <reference field="item_category_id" resource="supply_item_category">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="col[@field='Category']"/>
                        </xsl:attribute>
                    </reference>
                    <reference field="item_id" resource="supply_item">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="col[@field='Name']"/>
                        </xsl:attribute>
                    </reference>
	            </resource>
            </xsl:for-each>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>
