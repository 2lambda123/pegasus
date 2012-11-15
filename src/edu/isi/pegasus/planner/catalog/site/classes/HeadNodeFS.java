/*
 * 
 *   Copyright 2007-2008 University Of Southern California
 * 
 *   Licensed under the Apache License, Version 2.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 *   Unless required by applicable law or agreed to in writing,
 *   software distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 * 
 */

package edu.isi.pegasus.planner.catalog.site.classes;

import edu.isi.pegasus.planner.catalog.classes.Profiles;

import edu.isi.pegasus.planner.classes.Profile;


import java.io.Writer;
import java.io.IOException;

/**
 * This data class describes the HeadNode Filesystem layout.
 * 
 * @version $Revision$
 * @author Karan Vahi
 */
public class HeadNodeFS extends AbstractSiteData {

    /**
     * The scratch area on the head node.
     */
    private HeadNodeScratch mScratch;
     
    /**
     * The storage area on the head node.
     */ 
    private HeadNodeStorage mStorage;
    
    /**
     * The profiles associated with the headnode filesystem.
     */
    private Profiles mProfiles;
    
    
    /**
     * The default constructor.
     */
    public HeadNodeFS(){
        mScratch = new HeadNodeScratch();
        mStorage = new HeadNodeStorage();
        mProfiles= new Profiles();
    }
    
    /**
     * The overloaded constructor.
     * 
     * @param scratch  the scratch area.
     * @param storage  the storage area.
     */
    public HeadNodeFS( HeadNodeScratch scratch, HeadNodeStorage storage ){
        setScratch( scratch );
        setStorage( storage );
        mProfiles = new Profiles();
    }
    
    /**
     * Sets the scratch area on the head node.
     * 
     * @param scratch  the scratch area.
     */
    public void setScratch( HeadNodeScratch scratch ){
        mScratch = scratch;
    }
    
    /**
     * Selects a  <code>FileServer</code> associated with the Local Directory on
     * the Scratch system.
     * 
     * @return <FileServer> if specified, else null
     */
    public FileServer selectScratchLocalFileServer(){
        //return this.getScratch().getLocalDirectory().selectFileServer();
        HeadNodeScratch scratch = this.getScratch();
        if( scratch == null ){
            return null;
        }
        DirectoryLayout directory = scratch.getLocalDirectory();
        if( directory == null ){
            return null;
        }
        return directory.selectFileServer();
    }
    
    /**
     * Selects a  <code>FileServer</code> associated with the Shared Directory on
     * the Scratch system.
     * 
     * @return <FileServer> if specified, else null
     */
    public FileServer selectScratchSharedFileServer(){
        //return this.getScratch().getSharedDirectory().selectFileServer();
        HeadNodeScratch scratch = this.getScratch();
        if( scratch == null ){
            return null;
        }
        DirectoryLayout directory = scratch.getSharedDirectory();
        if( directory == null ){
            return null;
        }
        return directory.selectFileServer();
    }
    
    
    /**
     * Returns the scratch area on the head node.
     * 
     * @return the scratch area.
     */
    public HeadNodeScratch getScratch(  ){
        return this.mScratch;
    }
    
    /**
     * Sets the storage area on the head node.
     * 
     * @param storage  the storage area.
     */
    public void setStorage( HeadNodeStorage storage ){
        mStorage = storage;
    }
    
    /**
     * A convenience method that returns a file server to be used for stageout.
     * 
     * It selects a FileServer associated with the Local Directory.
     * If that is null, it then selects a FileServer associated with the 
     * Shared Directory.
     * 
     * @return  storage FileServer for stageout.
     */
    public FileServer selectStorageFileServerForStageout() {
        HeadNodeStorage s = this.getStorage();
        if( s == null ) { return null ; }
        
        FileServer fs = null;
        return ( (fs = this.selectStorageLocalFileServer()) == null)?
                  this.selectStorageSharedFileServer():  
                  fs;
    }

    
    /**
     * Selects a  <code>FileServer</code> associated with the Local Directory on
     * the Storage system.
     * 
     * @return <FileServer> if specified, else null
     */
    public FileServer selectStorageLocalFileServer(){
        //        return this.getStorage().getLocalDirectory().selectFileServer();
        StorageType storage = this.getStorage();
        if( storage == null ){
            return null;
        }
        DirectoryLayout directory = storage.getLocalDirectory();
        if( directory == null ){
            return null;
        }
        return directory.selectFileServer();
    }
    
    /**
     * Selects a  <code>FileServer</code> associated with the Shared Directory on
     * the Storage system.
     * 
     * @return <FileServer> if specified, else null
     */
    public FileServer selectStorageSharedFileServer(){
        //return this.getStorage().getSharedDirectory().selectFileServer();
        StorageType storage = this.getStorage();
        if( storage == null ){
            return null;
        }
        DirectoryLayout directory = storage.getSharedDirectory();
        if( directory == null ){
            return null;
        }
        return directory.selectFileServer();
    }
    
    /**
     * Returns the storage area on the head node.
     * 
     * @return the storage area.
     */
    public HeadNodeStorage getStorage(  ){
        return this.mStorage;
    }
    
    /**
     * Adds a profile.
     * 
     * @param p  the profile to be added
     */
    public void addProfile( Profile p ){
        //retrieve the appropriate namespace and then add
       mProfiles.addProfile(  p );
    }

    /**
     * Sets the profiles associated with the file server.
     * 
     * @param profiles   the profiles.
     */
    public void setProfiles( Profiles profiles ){
        mProfiles = profiles;
    }
    /**
     * Writes out the xml description of the object. 
     *
     * @param writer is a Writer opened and ready for writing. This can also
     *               be a StringWriter for efficient output.
     * @param indent the indent to be used.
     *
     * @exception IOException if something fishy happens to the stream.
     */
    public void toXML( Writer writer, String indent ) throws IOException {
        String newLine = System.getProperty( "line.separator", "\r\n" );
        String newIndent = indent + "\t";
        
        //write out the  xml element
        writer.write( indent );
        writer.write( "<head-fs>" );
        writer.write( newLine );
        
        this.getScratch().toXML( writer, newIndent );        
        this.getStorage().toXML( writer, newIndent );
        this.mProfiles.toXML( writer, newIndent );
        
        writer.write( indent );
        writer.write( "</head-fs>" );
        writer.write( newLine );
    }
    
    /**
     * Returns the clone of the object.
     *
     * @return the clone
     */
    public Object clone(){
        HeadNodeFS obj;
        try{
            obj = ( HeadNodeFS ) super.clone();
            obj.setScratch( (HeadNodeScratch)this.getScratch().clone() );
            obj.setStorage( (HeadNodeStorage)this.getStorage().clone() );
            obj.setProfiles( (Profiles)this.mProfiles.clone() );
            
        }
        catch( CloneNotSupportedException e ){
            //somewhere in the hierarch chain clone is not implemented
            throw new RuntimeException("Clone not implemented in the base class of " + this.getClass().getName(),
                                       e );
        }
        return obj;
    }

    
}
