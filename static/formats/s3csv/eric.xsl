<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
    
    <!-- **********************************************************************
         ERIC (Emergency Relief Item Catalog)  - CSV Import Stylesheet

         2011-06-20 / Michael Howden <michael AT aidiq DOT com>

         - use for import to supply/item resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be supply/item/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:
           
           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath
           
           You can add a third argument &ignore_errors
         CSV fields:
         item code.......................
         item description................
         length cm.......................
         height cm.......................
         width cm........................
         volume litre....................
         weight kg.......................
         in EIC.......................... If "yes" add to catalog "ERIC" too

        creates:
            supply_catalog...............
            supply_item_category.........
            supply_item..................
            supply_catalog_item..........
            
        @todo:

            - remove org_organisation (?)
            
    *********************************************************************** -->

    <xsl:output method="xml"/>

    <!-- Hardcoded Variables -->
    <xsl:variable name="OrgName">International Federation of Red Cross and Red Crescent Societies</xsl:variable>
    <xsl:variable name="OrgAcronym">IFRC</xsl:variable>
    
    <xsl:variable name="ERIC">ERIC</xsl:variable>
    <xsl:variable name="ERICComplete">ERIC - Complete</xsl:variable>

	<xsl:key name="item" match="row" use="col[@field='item code']"/>
	
    <xsl:template match="/">
        <s3xml>
            <resource name="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$OrgAcronym"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$OrgName"/></data>
                <data field="acronym"><xsl:value-of select="$OrgAcronym"/></data>
            </resource>
            
            <resource name="supply_catalog">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$ERIC"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$ERIC"/></data>
            </resource>
            
            <resource name="supply_catalog">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$ERICComplete"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$ERICComplete"/></data>
            </resource>
            
			<xsl:for-each select="//row[generate-id(.)=generate-id(key('item', col[@field='item code'])[1])]">
               <!-- Item -->
				<xsl:variable name="CategoryParent" select="substring(col[@field='item code']/text(),1,1)"/>
                <xsl:variable name="Category" select="substring(col[@field='item code']/text(),2,3)"/>
                <xsl:variable name="Code" select="col[@field='item code']/text()"/>
                <xsl:variable name="Name" select="col[@field='item description']/text()"/>
                <xsl:variable name="Length" select="col[@field='length cm']/text()"/>
                <xsl:variable name="Height" select="col[@field='height cm']/text()"/>
                <xsl:variable name="Width" select="col[@field='width cm']/text()"/>
                <xsl:variable name="Volume" select="col[@field='volume litre']/text()"/>
                <xsl:variable name="Weight" select="col[@field='weight kg']/text()"/>
                
                <xsl:variable name="InERIC" select="col[@field='in EIC']/text()"/>
                
                <resource name="supply_item">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Code"/>
                    </xsl:attribute>
                    <!-- Item Data -->
                    <data field="code"><xsl:value-of select="$Code"/></data>
                    <data field="name"><xsl:value-of select="$Name"/></data>
                    <data field="length"><xsl:value-of select="$Length"/></data>
                    <data field="height"><xsl:value-of select="$Height"/></data>
                    <data field="width"><xsl:value-of select="$Width"/></data>
                    <data field="volume"><xsl:value-of select="$Volume"/></data>
                    <data field="weight"><xsl:value-of select="$Weight"/></data>
                    
	                <!-- Catalog Item Components -->
	                <!-- ERIC - Complete-->
	                <resource name="supply_catalog_item">
	                    <!-- Link to Catalog -->
	                    <reference field="catalog_id" resource="supply_catalog">
	                        <xsl:attribute name="tuid">
	                            <xsl:value-of select="$ERICComplete"/>
	                        </xsl:attribute>
	                    </reference>
	                    
	                    <!-- Link to Category -->
	                    <reference field="item_category_id" resource="supply_item_category">
	                        <resource name="supply_item_category">
			                    <reference field="catalog_id" resource="supply_catalog">
			                        <xsl:attribute name="tuid">
			                            <xsl:value-of select="$ERICComplete"/>
			                        </xsl:attribute>
			                    </reference>
			                    
		                        <reference field="parent_item_category_id" resource="supply_item_category">
		                        	<resource name="supply_item_category">
					                    <reference field="catalog_id" resource="supply_catalog">
					                        <xsl:attribute name="tuid">
					                            <xsl:value-of select="$ERICComplete"/>
					                        </xsl:attribute>
					                    </reference>
					                    <data field="code"><xsl:value-of select="$CategoryParent"/></data>
					            	</resource>
		                        </reference>
		                        
	                        	<data field="code"><xsl:value-of select="$Category"/></data>
	                        </resource>
	                    </reference>
	                    <!-- Must include a field (workaround) -->
	                    <data field="comments">_</data>
	                </resource>
	                 <!-- ERIC -->
	                 <xsl:if test="$InERIC = 'yes'">
		                 <resource name="supply_catalog_item">
		                    <!-- Link to Catalog -->
		                    <reference field="catalog_id" resource="supply_catalog">
		                        <xsl:attribute name="tuid">
		                            <xsl:value-of select="$ERIC"/>
		                        </xsl:attribute>
		                    </reference>
		                    
		                    <!-- Link to Category -->
		                    <reference field="item_category_id" resource="supply_item_category">
		                        <resource name="supply_item_category">
				                    <reference field="catalog_id" resource="supply_catalog">
				                        <xsl:attribute name="tuid">
				                            <xsl:value-of select="$ERICComplete"/>
				                        </xsl:attribute>
				                    </reference>
				                    
			                        <reference field="parent_item_category_id" resource="supply_item_category">
			                        	<resource name="supply_item_category">
						                    <reference field="catalog_id" resource="supply_catalog">
						                        <xsl:attribute name="tuid">
						                            <xsl:value-of select="$ERICComplete"/>
						                        </xsl:attribute>
						                    </reference>
						                    <data field="code"><xsl:value-of select="$CategoryParent"/></data>
						            	</resource>
			                        </reference>
			                        
		                        	<data field="code"><xsl:value-of select="$Category"/></data>
		                        </resource>
		                    </reference>
		                    <!-- Must include a field (workaround) -->
		                    <data field="comments">_</data>
		                 </resource>
	                 </xsl:if>
                </resource>
            </xsl:for-each>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>
