/**
 * Copyright 2007-2008 University Of Southern California
 *
 * <p>Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file
 * except in compliance with the License. You may obtain a copy of the License at
 *
 * <p>http://www.apache.org/licenses/LICENSE-2.0
 *
 * <p>Unless required by applicable law or agreed to in writing, software distributed under the
 * License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 */
package edu.isi.pegasus.planner.transfer;

import edu.isi.pegasus.planner.classes.FileTransfer;
import edu.isi.pegasus.planner.classes.Job;
import edu.isi.pegasus.planner.classes.PegasusBag;
import edu.isi.pegasus.planner.refiner.ReplicaCatalogBridge;
import edu.isi.pegasus.planner.transfer.implementation.TransferImplementationFactoryException;
import java.util.Collection;

/**
 * The refiner interface, that determines the functions that need to be implemented to add various
 * types of transfer nodes to the workflow.
 *
 * @author Karan Vahi
 * @author Gaurang Mehta
 * @version $Revision$
 */
public interface Refiner
        extends edu.isi.pegasus.planner.refiner
                .Refiner { // need to extend it for the PASOA integration

    /** The prefix for all local transfer jobs. */
    public static final String LOCAL_PREFIX = "local_";

    /** The prefix for all remote transfer jobs */
    public static final String REMOTE_PREFIX = "remote_";

    /**
     * The prefix for the jobs which are added to transfer the files to a job's execution pool from
     * the location returned from the replica mechanism. the new job's name is FROM_RC_PREFIX +
     * nameofjob + _+ counter.
     */
    public static final String STAGE_IN_PREFIX = "stage_in_";

    /** The prefix for the jobs that symlink against existing input data on a compute site. */
    // public static final String SYMBOLIC_LINK_PREFIX = "symlink_";

    /**
     * The prefix for the jobs which are added to transfer the files generated by a job on an
     * execution pool to the output pool. The new job's name is TO_RC_PREFIX + nameofjob + _+
     * counter.
     */
    public static final String STAGE_OUT_PREFIX = "stage_out_";

    /**
     * The prefix for the jobs which are added to transfer the files generated by the parents of a
     * job to the jobs execution pool. The new job's name is INTER_POOL_PREFIX + nameofjob + _+
     * counter.
     */
    public static final String INTER_POOL_PREFIX = "stage_inter_";

    /**
     * The prefix for the jobs which register the newly materialized files in the Replica Catalog.
     * The job's name should be RC_REGISTER_PREFIX + nameofjob, where nameofjob is the job that
     * generates these materialized files.
     */
    public static final String REGISTER_PREFIX = "register_";

    /**
     * Loads the appropriate implementations that is required by this refinement strategy for
     * different types of transfer jobs. It calls to the factory method to load the appropriate
     * Implementor.
     *
     * <p>Loads the implementing class corresponding to the mode specified by the user at runtime in
     * the properties file. The properties object passed should not be null.
     *
     * @param bag the bag of initialization objects.
     * @throws org.griphyn.cPlanner.transfer.implementation.TransferImplementationFactoryException
     */
    public void loadImplementations(PegasusBag bag) throws TransferImplementationFactoryException;

    /**
     * Adds the inter pool transfer nodes that are required for transferring the output files of the
     * parents to the jobs execution site.
     *
     * @param job <code>Job</code> object corresponding to the node to which the files are to be
     *     transferred to.
     * @param files Collection of <code>FileTransfer</code> objects containing the information about
     *     source and destURL's.
     * @param localTransfer boolean indicating that associated transfer job will run on local site.
     */
    public void addInterSiteTXNodes(Job job, Collection files, boolean localTransfer);

    /**
     * Adds the stageout transfer nodes, that stage data to an output site specified by the user.
     *
     * @param job <code>Job</code> object corresponding to the node to which the files are to be
     *     transferred to.
     * @param files Collection of <code>FileTransfer</code> objects containing the information about
     *     source and destURL's.
     * @param rcb bridge to the Replica Catalog. Used for creating registration nodes in the
     *     workflow.
     * @param localTransfer boolean indicating that associated transfer job will run on local site.
     */
    public void addStageOutXFERNodes(
            Job job, Collection files, ReplicaCatalogBridge rcb, boolean localTransfer);

    /**
     * Adds the stageout transfer nodes, that stage data to an output site specified by the user. It
     * also adds the registration nodes to register the data in the replica catalog if required.
     *
     * @param job <code>Job</code> object corresponding to the node to which the files are to be
     *     transferred to.
     * @param files Collection of <code>FileTransfer</code> objects containing the information about
     *     source and destURL's.
     * @param rcb bridge to the Replica Catalog. Used for creating registration nodes in the
     *     workflow.
     * @param localTransfer boolean indicating that associated transfer job will run on local site.
     * @param deletedLeaf to specify whether the node is being added for a deleted node by the
     *     reduction engine or not. default: false
     */
    public abstract void addStageOutXFERNodes(
            Job job,
            Collection files,
            ReplicaCatalogBridge rcb,
            boolean localTransfer,
            boolean deletedLeaf);

    /**
     * Adds the stage in transfer nodes which transfer the input files for a job, from the location
     * returned from the replica catalog to the job's execution pool.
     *
     * @param job <code>Job</code> object corresponding to the node to which the files are to be
     *     transferred to.
     * @param files Collection of <code>FileTransfer</code> objects containing the information about
     *     source and destURL's.
     * @param symLinkFiles Collection of <code>FileTransfer</code> objects containing source and
     *     destination file url's for symbolic linking on compute site.
     */
    public void addStageInXFERNodes(
            Job job, Collection<FileTransfer> files, Collection<FileTransfer> symLinkFiles);

    /**
     * Signals that the traversal of the workflow is done. This would allow the transfer mechanisms
     * to clean up any state that they might be keeping that needs to be explicitly freed.
     */
    public void done();

    /**
     * Boolean indicating whether the Transfer Refiner has a preference for where a transfer job is
     * run.
     *
     * @return boolean
     */
    public boolean refinerPreferenceForTransferJobLocation();

    /**
     * Boolean indicating Refiner preference for transfer jobs to run locally. This method should be
     * called only if refinerPreferenceForTransferJobLocation is true for a refiner.
     *
     * @param type the type of transfer job for which the URL is being constructed. Should be one of
     *     the following: stage-in stage-out inter-pool transfer
     * @return boolean refiner preference for transfer job to run locally or not.
     */
    public boolean refinerPreferenceForLocalTransferJobs(int type);

    /**
     * Returns whether a Site prefers transfers to be run on it i.e remote transfers enabled.
     *
     * @param site the name of the site.
     * @param type the type of transfer job for which the URL is being constructed. Should be one of
     *     the following: stage-in stage-out inter-pool transfer
     * @return true if site is setup for remote transfers
     * @see Job#STAGE_IN_JOB
     * @see Job#INTER_POOL_JOB
     * @see Job#STAGE_OUT_JOB
     */
    public boolean runTransferRemotely(String site, int type);

    /**
     * Returns whether a Site is third party enabled or not.
     *
     * @param site the name of the site.
     * @param type the type of transfer job for which the URL is being constructed. Should be one of
     *     the following: stage-in stage-out inter-pool transfer
     * @return true pool is third party enabled false pool is not third party enabled.
     * @see Job#STAGE_IN_JOB
     * @see Job#INTER_POOL_JOB
     * @see Job#STAGE_OUT_JOB
     */
    public boolean isSiteThirdParty(String site, int type);

    /**
     * Returns whether the third party transfers for a particular site are to be run on the remote
     * site or the submit host.
     *
     * @param site the name of the site.
     * @param type the type of transfer job for which the URL is being constructed. Should be one of
     *     the following: stage-in stage-out inter-pool transfer
     * @return true if the transfers are to be run on remote site, else false.
     * @see Job#STAGE_IN_JOB
     * @see Job#INTER_POOL_JOB
     * @see Job#STAGE_OUT_JOB
     */
    public boolean runTPTOnRemoteSite(String site, int type);

    /**
     * Add a new job to the workflow being refined.
     *
     * @param job the job to be added.
     */
    public void addJob(Job job);

    /**
     * Adds a new relation to the workflow being refiner.
     *
     * @param parent the jobname of the parent node of the edge.
     * @param child the jobname of the child node of the edge.
     */
    public void addRelation(String parent, String child);

    /**
     * Adds a new relation to the workflow. In the case when the parent is a transfer job that is
     * added, the parentNew should be set only the first time a relation is added. For subsequent
     * compute jobs that maybe dependant on this, it needs to be set to false.
     *
     * @param parent the jobname of the parent node of the edge.
     * @param child the jobname of the child node of the edge.
     * @param pool the execution pool where the transfer node is to be run.
     * @param parentNew the parent node being added, is the new transfer job and is being called for
     *     the first time.
     */
    public void addRelation(String parent, String child, String pool, boolean parentNew);

    /**
     * Returns a textual description of the transfer mode.
     *
     * @return a short textual description
     */
    public String getDescription();
}
