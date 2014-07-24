/**
 *  Copyright 2007-2008 University Of Southern California
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *  http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing,
 *  software distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */

package edu.isi.pegasus.planner.refiner;

import edu.isi.pegasus.planner.catalog.site.classes.SiteCatalogEntry;

import edu.isi.pegasus.planner.classes.ADag;
import edu.isi.pegasus.planner.classes.Job;
import edu.isi.pegasus.planner.classes.PegasusBag;

import edu.isi.pegasus.common.logging.LogManager;
import edu.isi.pegasus.common.util.PegasusURL;

import edu.isi.pegasus.planner.catalog.transformation.TransformationCatalogEntry;

import edu.isi.pegasus.planner.catalog.transformation.classes.TCType;

import edu.isi.pegasus.common.util.Separator;

import edu.isi.pegasus.planner.catalog.site.classes.FileServer;
import edu.isi.pegasus.planner.classes.TransferJob;
import java.util.Iterator;
import java.util.Set;
import java.util.List;
import java.util.LinkedList;

import java.io.File;
import edu.isi.pegasus.planner.namespace.Pegasus;
import edu.isi.pegasus.planner.partitioner.graph.GraphNode;
import edu.isi.pegasus.planner.refiner.createdir.AbstractStrategy;
import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.BitSet;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.Map;


/**
 * Ends up creating a cleanup dag that deletes the remote directories that
 * were created by the create dir jobs. The cleanup dag is generated in a
 * sub directory from the main directory containing the submit files of the
 * dag. The dag consists of independant jobs, with each job responsible for
 * deleting directory for a execution pool. The current way of generating the
 * dag is tied to the fact, that the directories in which a job are executed
 * is tied to the pool not the job itself.
 *
 * @author Karan Vahi
 * @version $Revision$
 * @see CreateDirectory
 */
public class RemoveDirectory extends Engine {



    /**
     * The prefix that is attached to the name of the dag for which the
     * cleanup Dag is being generated, to generate the name of the cleanup
     * Dag.
     */
    public static final String CLEANUP_DAG_PREFIX = "del_";

    /**
     * Constant suffix for the names of the remote directory nodes.
     */
    public static final String REMOVE_DIR_SUFFIX = "_rdir";

    /**
     * The logical name of the transformation that removes directories on the
     * remote execution pools.
     */
    public static final String TRANSFORMATION_NAME = "cleanup";
    
    
    /**
     * The basename of the pegasus dirmanager  executable.
     */
    public static final String REMOVE_DIR_EXECUTABLE_BASENAME = "pegasus-cleanup";

    /**
     * The transformation namespace for the create dir jobs.
     */
    public static final String TRANSFORMATION_NAMESPACE = "pegasus";

    /**
     * The version number for the derivations for create dir  jobs.
     */
    public static final String TRANSFORMATION_VERSION = null;

    /**
     * The derivation namespace for the create dir  jobs.
     */
    public static final String DERIVATION_NAMESPACE = "pegasus";

    /**
     * The logical name of the transformation that removes directories on the
     * remote execution pools.
     */
    public static final String DERIVATION_NAME = "cleanup";


    /**
     * The version number for the derivations for create dir  jobs.
     */
    public static final String DERIVATION_VERSION = "1.0";

    /**
     * Constant suffix for the names of the deployment nodes.
     */
    public static final String CLEANUP_PREFIX = "cleanup_";

    /**
     * The concrete dag so far, for which the clean up dag needs to be generated.
     */
    private ADag mConcDag;


    /**
     *  Boolean indicating whether we need to transfer dirmanager from the submit
     * host.
     */
    private boolean mTransferFromSubmitHost;
    
    /**
     * A convenience method to return the complete transformation name being
     * used to construct jobs in this class.
     *
     * @return the complete transformation name
     */
    public static String getCompleteTranformationName(){
        return Separator.combine( TRANSFORMATION_NAMESPACE,
                                  TRANSFORMATION_NAME,
                                  TRANSFORMATION_VERSION );
    }

    /**
     * The submit directory for the workflow.
     */
    private  String mSubmitDirectory;

    
    /**
     * The job prefix that needs to be applied to the job file basenames.
     */
    protected String mJobPrefix;
    
    /**
     * The overloaded constructor that sets the dag for which we have to
     * generated the cleanup dag for.
     *
     * @param concDag  the concrete dag for which cleanup is reqd.
     * @param bag      the bag of initialization objects
     * @param submitDirectory   the submit directory for the cleanup workflow
     */
    public RemoveDirectory( ADag concDag, PegasusBag bag, String submitDirectory ) {
        super( bag );
        mConcDag = concDag;
        mTransferFromSubmitHost = bag.getPegasusProperties().transferWorkerPackage();
        mSubmitDirectory = submitDirectory;
        
        mJobPrefix  = bag.getPlannerOptions().getJobnamePrefix();
    }

    /**
     * Modifies the workflow to add remove directory nodes. The workflow passed
     * is a worklow, where the jobs have been mapped to sites.
     * 
     * The strategy involves in walking the graph in a BFS order, and updating a 
     * bit set associated with each job based on the BitSet of the parents jobs. 
     * The BitSet indicates whether an edge exists from the descendant of a node
     * to the remove dir job.
     * 
     * For a node, the bit set is the union of all the parents BitSets. The BFS 
     * traversal ensures that the bitsets are of a node are only updated once the 
     * parents have been processed.
     * 
     * @param dag   the workflow to which the nodes have to be added.
     * 
     * @return the added workflow
     */
    public ADag addRemoveDirectoryNodes( ADag dag ){
        //PM-747 no need for conversion as ADag now implements Graph interface
        return this.addRemoveDirectoryNodes( dag  ,this.getCreateDirSites(dag));
    }
    
    /**
     * Adds create dir nodes to the workflow.
     * 
     * The strategy involves in walking the graph in a BFS order, and updating a 
     * bit set associated with each job based on the BitSet of the parent jobs. 
     * The BitSet indicates whether an edge exists from the create dir job to an 
     * ancestor of the node.
     * 
     * For a node, the bit set is the union of all the parents BitSets. The BFS 
     * traversal ensures that the bitsets are of a node are only updated once the 
     * parents have been processed.
     * 
     * @param workflow  the workflow 
     * @param sites     the staging sites the workflow refers to.
     * 
     * @return 
     */
    public ADag addRemoveDirectoryNodes( ADag workflow, Set<String> sites ) {
        //the number of sites dictates the size of the BitSet associated with each job.
        Map<String, Integer> siteToBitIndexMap = new HashMap();
        int bitSetSize = sites.size();
        int i = 0;
        for( String site: sites ){
            siteToBitIndexMap.put( site, i++ );
        }
        
        
        //create the remove dir jobs required but don't add to the workflow
        //till edges are figured out
        //for each execution pool add a remove directory node.
        Map<GraphNode,List<GraphNode>> removeDirParentsMap = new HashMap();
        Map<String,GraphNode> removeDirMap = new HashMap();//mas site to the associated remove dir node
        for (String site: sites ){
            String jobName = getRemoveDirJobName( workflow, site );
            Job newJob  = this.makeRemoveDirJob( site, jobName );
            mLogger.log( "Creating remove directory node " + jobName , LogManager.DEBUG_MESSAGE_LEVEL );
            GraphNode node = new GraphNode( newJob.getID() );
            node.setContent(newJob);
            removeDirParentsMap.put(node, new LinkedList<GraphNode>());
            removeDirMap.put( site, node );
        }
        
        
        //we use an identity hash map to associate the nodes with the bitmaps 
        Map<GraphNode,BitSet> nodeBitMap = new IdentityHashMap( workflow.size() );
        
        //do a BFS walk over the workflow
        for( Iterator<GraphNode> it = workflow.bottomUpIterator(); it.hasNext(); ){
            GraphNode node = it.next();
            BitSet set     = new BitSet( bitSetSize );
            Job job        = (Job)node.getContent();
            String site    = getAssociatedCreateDirSite( job );
            
            //check if for stage out jobs there are any parents specified 
            //or not.
            if( job instanceof TransferJob && job.getJobType() == Job.STAGE_OUT_JOB ){
                if( node.getParents().isEmpty() ){
                    //means we have a stage out job only. probably the workflow
                    //was fully reduced in data reuse
                    mLogger.log( "Not considering job for remove dir edges " + job.getID() , LogManager.DEBUG_MESSAGE_LEVEL );
                    nodeBitMap.put(node, set);
                    continue;
                }
            }
            
            if( job.getJobType() == Job.CREATE_DIR_JOB ){
                //no need to do anything for the create dir jobs
                continue;
            }
            
            //the set is a union of all the parents set
            for( GraphNode child: node.getChildren()){
                BitSet cSet = nodeBitMap.get( child );
                set.or( cSet );
            }
            
            if( site == null ){
                //only ok for stage worker jobs
                if( job instanceof TransferJob || job.getJobType() == Job.REPLICA_REG_JOB ){
                    mLogger.log( "Not adding edge to create dir job for job " + job.getID(),
                                     LogManager.DEBUG_MESSAGE_LEVEL );
                    nodeBitMap.put(node, set);
                    continue;
                }
                else{
                    throw new RuntimeException( "Job not associated with staging site " + job.getID() );
                }
            }
            
          
            //System.out.println( "Create dir site for job " + job.getID() + " is " + site );


            int index = siteToBitIndexMap.get( site );
            if(! set.get( index ) ){
                //none of the parents have an index to the site
                //need to add an edge.
                GraphNode child = removeDirMap.get( site );
                mLogger.log( "Need to add edge "  + job.getID() + " -> " + child.getID(),
                             LogManager.DEBUG_MESSAGE_LEVEL );
                removeDirParentsMap.get( child ).add( node );

                //edge has been added . set the bit to true
                set.set( index );
            }
            
            //set the bitset of remove dirs for the node
            nodeBitMap.put(node, set);
        }
        
        
        //for each create dir job add it to the workflow
        //and connect the edges
        for ( Map.Entry<GraphNode, List<GraphNode>> entry : removeDirParentsMap.entrySet()  ){
            GraphNode removeDirNode = entry.getKey();
            List<GraphNode> parents = entry.getValue();
            mLogger.log(  "Adding node to the worklfow " + removeDirNode.getID(),
                          LogManager.DEBUG_MESSAGE_LEVEL );
            for( GraphNode parent: parents ){
                removeDirNode.addParent(parent);
                parent.addChild( removeDirNode );
            }
            workflow.addNode( removeDirNode );

        }

        
        return workflow;
    }

    /**
     * Retrieves the sites for which the create dir jobs need to be created.
     * It returns all the sites where the compute jobs have been scheduled.
     *
     *
     * @return  a Set containing a list of siteID's of the sites where the
     *          dag has to be run.
     */
    protected Set getCreateDirSites( ADag dag ){
        return AbstractStrategy.getCreateDirSites(dag);
    }


    /**
     * It returns the name of the remove directory job, that is to be assigned.
     * The name takes into account the workflow name while constructing it, as
     * that is thing that can guarentee uniqueness of name in case of deferred
     * planning.
     *
     * @param dag   the dag for which the cleanup DAG is being generated.
     * @param site  the execution site for which the remove directory job
     *              is responsible.
     *
     * @return String corresponding to the name of the job.
     */
    private String getRemoveDirJobName(ADag dag,String site){
        StringBuffer sb = new StringBuffer();

        //append setup prefix
        sb.append( DeployWorkerPackage.CLEANUP_PREFIX );
        //append the job prefix if specified in options at runtime
        if ( mJobPrefix != null ) { sb.append( mJobPrefix ); }

        sb.append( dag.getLabel() ).append( "_" ).
           append( dag.getIndex() ).append( "_" );


        sb.append( site );

        return sb.toString();
    }


    /**
     * It creates a remove directory job that creates a directory on the remote pool
     * using the perl executable that Gaurang wrote. It access mkdir underneath.
     * It gets the name of the random directory from the Pool handle.
     *
     * @param site  the execution pool for which the create dir job is to be
     *                  created.
     * @param jobName   the name that is to be assigned to the job.
     *
     * @return the remove dir job.
     */
    public Job makeRemoveDirJob( String site, String jobName ) {
        
        List<String> l = new LinkedList<String>();

        //the externally accessible url to the directory/ workspace for the workflow
        l.add( mSiteStore.getExternalWorkDirectoryURL( site, FileServer.OPERATION.put )  );
        return makeRemoveDirJob( site, jobName, l  );
    }
    
    /**
     * It creates a remove directory job that creates a directory on the remote pool
     * using the perl executable that Gaurang wrote. It access mkdir underneath.
     * It gets the name of the random directory from the Pool handle.
     *
     * @param site      the site from where the directory need to be removed.
     * @param jobName   the name that is to be assigned to the job.
     * @param files  the list of files to be cleaned up.
     *
     * @return the remove dir job.
     */
    public Job makeRemoveDirJob( String site, String jobName, List<String> files ) {
        Job newJob  = new Job();
        List entries    = null;
        String execPath = null;
        TransformationCatalogEntry entry   = null;



        //the site where the cleanup job will run
        String eSite = "local";

        for( String file: files ){
            if( file.startsWith( PegasusURL.FILE_URL_SCHEME ) ){
                //means the cleanup job should run on the staging site
                mLogger.log( "Directory URL is a file url for site " + site + "  " +  files,
                                 LogManager.DEBUG_MESSAGE_LEVEL );
                eSite = site;
            }
        }

        SiteCatalogEntry ePool = mSiteStore.lookup( eSite );

        try {
            entries = mTCHandle.lookup( RemoveDirectory.TRANSFORMATION_NAMESPACE,
                                              RemoveDirectory.TRANSFORMATION_NAME,
                                              RemoveDirectory.TRANSFORMATION_VERSION,
                                              eSite,
                                              TCType.INSTALLED);
        }
        catch (Exception e) {
            //non sensical catching
            mLogger.log("Unable to retrieve entry from TC " + e.getMessage(),
                        LogManager.DEBUG_MESSAGE_LEVEL );
        }
        entry = ( entries == null ) ?
                     this.defaultTCEntry( ePool ): //try using a default one
                     (TransformationCatalogEntry) entries.get(0);


        if( entry == null ){
            //NOW THROWN AN EXCEPTION

            //should throw a TC specific exception
            StringBuffer error = new StringBuffer();
            error.append("Could not find entry in tc for lfn ").
                  append( this.getCompleteTranformationName() ).
                  append(" at site ").append( eSite );

            mLogger.log( error.toString(), LogManager.ERROR_MESSAGE_LEVEL);
            throw new RuntimeException( error.toString() );
        }
        if( mTransferFromSubmitHost ){
            /*
            //we are using mkdir directly
            argString = " -p " + mPoolHandle.getExecPoolWorkDir( execPool );
            execPath  = "mkdir";
            //path variable needs to be set
            newJob.envVariables.construct( "PATH", CreateDirectory.PATH_VALUE );
            */
            newJob.vdsNS.construct( Pegasus.GRIDSTART_KEY, "None" );

            StringBuffer sb = new StringBuffer();
            sb.append( mProps.getBinDir() ).
               append( File.separator ).append( RemoveDirectory.REMOVE_DIR_EXECUTABLE_BASENAME );
            execPath = sb.toString();
            newJob.condorVariables.construct( "transfer_executable", "true" );
        }
        else{
            execPath = entry.getPhysicalTransformation();
        }


        //prepare the stdin for the cleanup job
        String stdIn = jobName + ".in";
        try{
            BufferedWriter writer;
            writer = new BufferedWriter( new FileWriter(
                                        new File( mSubmitDirectory, stdIn ) ));

            int fileNum = 1;
            for( String file: files ){
                writer.write( "# " + fileNum + " " + site );
                writer.write( "\n" );
                writer.write( file );
                writer.write( "\n" );
                
                //associate a credential if required
                newJob.addCredentialType( site, file );
            }

            //closing the handle to the writer
            writer.close();
        }
        catch(IOException e){
            mLogger.log( "While writing the stdIn file " + e.getMessage(),
                        LogManager.ERROR_MESSAGE_LEVEL);
            throw new RuntimeException( "While writing the stdIn file " + stdIn, e );
        }

        //set the stdin file for the job
        newJob.setStdIn( stdIn );
        
        newJob.jobName = jobName;
        newJob.setTransformation( RemoveDirectory.TRANSFORMATION_NAMESPACE,
                                  RemoveDirectory.TRANSFORMATION_NAME,
                                  RemoveDirectory.TRANSFORMATION_VERSION );

        newJob.setDerivation( RemoveDirectory.DERIVATION_NAMESPACE,
                              RemoveDirectory.DERIVATION_NAME,
                              RemoveDirectory.DERIVATION_VERSION  );


        newJob.executable = execPath;
        newJob.setSiteHandle( eSite );
        newJob.jobClass = Job.CLEANUP_JOB;
        newJob.jobID = jobName;

        //PM-150 for leaf cleanup nodes we will set a specific recursive flag
        newJob.setArguments( " --recursive " );
        
        //the profile information from the pool catalog needs to be
        //assimilated into the job.
        newJob.updateProfiles( mSiteStore.lookup( newJob.getSiteHandle() ).getProfiles() );

        //add any notifications specified in the transformation
        //catalog for the job. JIRA PM-391
        newJob.addNotifications( entry );

        //the profile information from the transformation
        //catalog needs to be assimilated into the job
        //overriding the one from pool catalog.
        newJob.updateProfiles(entry);

        //the profile information from the properties file
        //is assimilated overidding the one from transformation
        //catalog.
        newJob.updateProfiles(mProps);


        return newJob;

    }



    /**
     * Returns a default TC entry to be used in case entry is not found in the
     * transformation catalog.
     *
     * @param site   the SiteCatalogEntry for the site for which the default entry is required.
     *
     *
     * @return  the default entry.
     */
    private  TransformationCatalogEntry defaultTCEntry( SiteCatalogEntry site ){
        TransformationCatalogEntry defaultTCEntry = null;
        //check if PEGASUS_HOME is set
        String home = site.getPegasusHome();
        //if PEGASUS_HOME is not set, use VDS_HOME
        home = ( home == null )? site.getVDSHome( ): home;

        mLogger.log( "Creating a default TC entry for " +
                     RemoveDirectory.getCompleteTranformationName() +
                     " at site " + site.getSiteHandle(),
                     LogManager.DEBUG_MESSAGE_LEVEL );

        //if home is still null
        if ( home == null ){
            //cannot create default TC
            mLogger.log( "Unable to create a default entry for " +
                         RemoveDirectory.getCompleteTranformationName(),
                         LogManager.DEBUG_MESSAGE_LEVEL );
            //set the flag back to true
            return defaultTCEntry;
        }

        //remove trailing / if specified
        home = ( home.charAt( home.length() - 1 ) == File.separatorChar )?
            home.substring( 0, home.length() - 1 ):
            home;

        //construct the path to it
        StringBuffer path = new StringBuffer();
        path.append( home ).append( File.separator ).
            append( "bin" ).append( File.separator ).
            append( RemoveDirectory.REMOVE_DIR_EXECUTABLE_BASENAME );


        defaultTCEntry = new TransformationCatalogEntry( RemoveDirectory.TRANSFORMATION_NAMESPACE,
                                                         RemoveDirectory.TRANSFORMATION_NAME,
                                                         RemoveDirectory.TRANSFORMATION_VERSION );

        defaultTCEntry.setPhysicalTransformation( path.toString() );
        defaultTCEntry.setResourceId( site.getSiteHandle() );
        defaultTCEntry.setType( TCType.INSTALLED );
        defaultTCEntry.setSysInfo( site.getSysInfo() );

        //register back into the transformation catalog
        //so that we do not need to worry about creating it again
        try{
            mTCHandle.insert( defaultTCEntry , false );
        }
        catch( Exception e ){
            //just log as debug. as this is more of a performance improvement
            //than anything else
            mLogger.log( "Unable to register in the TC the default entry " +
                          defaultTCEntry.getLogicalTransformation() +
                          " for site " + site, e,
                          LogManager.DEBUG_MESSAGE_LEVEL );
        }

        return defaultTCEntry;
    }

    /**
     * Returns the associated site that job is dependant on.
     * This is site, whose create dir job should be a parent or an ancestor of 
     * the job.
     * 
     * @param job  the job for which we need the associated create dir site.
     * 
     * @return the site 
     */
    private String getAssociatedCreateDirSite( Job job ) {
        String site = null;
        if( job.getJobType() == Job.CHMOD_JOB ){
            site =  job.getSiteHandle();
        }
        else{
            //the parent in case of a transfer job
            //is the non third party site
            site = ( job instanceof TransferJob )?
                               ((TransferJob)job).getNonThirdPartySite():
                               job.getStagingSiteHandle();

            
            if( site == null ){
                //only ok for stage worker jobs
                if( job instanceof TransferJob ){
                    mLogger.log( "Not adding edge to create dir job for job " + job.getID(),
                                     LogManager.DEBUG_MESSAGE_LEVEL );
                    return site;
                    
                }
            }
        }
        return site;
    }

}
