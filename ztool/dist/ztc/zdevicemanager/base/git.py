from .zrequests import *
import re
import pygit2
import urllib.parse

# hack for pygit2 gc issue on __del__ remote
# TODO: investigate better
pygit2_remote_del = pygit2.Remote.__del__

def pygit2_newremote_del(self):
    try:
        pygit2_remote_del(self)
    except Exception as e:
        pass

pygit2.Remote.__del__ = pygit2_newremote_del
# end of hack

__all__=['git']

class Git():
    push_error = False
    def __init__(self):        
        self.GIT_BRANCH_LOCAL               = pygit2.GIT_BRANCH_LOCAL
        self.GIT_BRANCH_REMOTE              = pygit2.GIT_BRANCH_REMOTE
        self.GIT_MERGE_ANALYSIS_UP_TO_DATE  = pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE
        self.GIT_MERGE_ANALYSIS_FASTFORWARD = pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD
        self.GIT_MERGE_ANALYSIS_NORMAL      = pygit2.GIT_MERGE_ANALYSIS_NORMAL
        self.GIT_OBJ_COMMIT                 = pygit2.GIT_OBJ_COMMIT

    def get_repo(self, path, no_fatal=False):
        try:
            repo_path = pygit2.discover_repository(path)
            repo = pygit2.Repository(repo_path)
            if "user.name" not in repo.config:
                repo.config["user.name"] = "Zerynth User"
            if "user.email" not in repo.config:
                repo.config["user.email"] = "zuser@zerynth.com"
            return repo
        except Exception as e:
            if no_fatal:
                raise e
            else:
                fatal("No repository at",path,e)

    def get_remote(self,repo,remote):
        try:
            res = repo.remotes[remote]
            token = get_token(True)
            if not token:
                fatal("Invalid token!")
            if token not in res.url:
                #update credentials
                ccu = re.compile("https{0,1}://([^:]*)(.*)")
                mth = ccu.match(res.url)
                newurl = res.url.replace(mth.group(1),token)
                repo.remotes.set_url(remote,newurl)
                res = repo.remotes[remote]
            return res
        except Exception as e:
            fatal("No such remote:",remote,e)

    def create_remote(self,path,remote,url):
        repo = self.get_repo(path)
        try:
            res = repo.remotes[remote]
            repo.remotes.set_url(remote, url)
        except:
            repo.remotes.create(remote, url)
            

    def git_push(self,path,remote,refspec=None,zcreds=True):
        repo = self.get_repo(path)
        if zcreds:
            r = self.get_remote(repo,remote)
        else:
            r = repo.remotes[remote]
        Git.push_error = False

        class PushCallback(pygit2.RemoteCallbacks):
            @staticmethod
            def push_update_reference(refname,message):
                if message:
                    Git.push_error="Backend refused to accept this push! ("+message+")"

        info("Pushing changes to remote repository...")
        try:
            ref = [repo.head.name] if refspec is None else [refspec.name]
            r.push(ref,PushCallback())
            if Git.push_error: raise Exception(Git.push_error)
        except pygit2.GitError as e:
            fatal(str(e))
        except Exception as e:
            fatal(str(e))
        info("Ok")

    def git_pull(self,path,remote):
        repo = self.get_repo(path)
        r = self.get_remote(repo,remote)
        info("Fetching remote...")
        try:
            r.fetch()
        except pygit2.GitError as e:
            fatal(str(e))
        remote_master_id = repo.lookup_reference('refs/remotes/'+remote+'/'+repo.head.shorthand).target
        merge_result, _ = repo.merge_analysis(remote_master_id)
        
        # Up to date, do nothing
        if merge_result & self.GIT_MERGE_ANALYSIS_UP_TO_DATE:
            info("Up to date, nothing to pull")
            return
        # We can just fastforward
        elif merge_result & self.GIT_MERGE_ANALYSIS_FASTFORWARD:
            repo.checkout_tree(repo.get(remote_master_id))
            master_ref = repo.lookup_reference('refs/heads/'+repo.head.shorthand)
            master_ref.set_target(remote_master_id)
            repo.head.set_target(remote_master_id)
            info("Merging remote to local repository...")
        elif merge_result & self.GIT_MERGE_ANALYSIS_NORMAL:
            info("Merging remote to local repository...")
            repo.merge(remote_master_id)
            if repo.index.conflicts:
                for k in repo.index.conflicts:
                    info("Conflict:",k)
                fatal("There are conflicts! Resolve them manually")
            else:
                info("Committing merge...")
                user = repo.default_signature
                tree = repo.index.write_tree()
                commit = repo.create_commit('HEAD',
                                                user,
                                                user,
                                                'Merge',
                                                tree,
                                                [repo.head.target, remote_master_id])
                repo.state_cleanup()
        info("Ok")

    def git_branch(self,path,branch,remote):
        repo = self.get_repo(path)
        r = self.get_remote(repo,remote)
        for b in repo.listall_branches(self.GIT_BRANCH_LOCAL):
            if b==branch:
                repo.checkout(repo.lookup_branch(b))
                info("Switched to branch",b)
                break
        else:
            # create new and set upstream
            repo.create_branch(branch,repo.head.get_object())
            info("Created new branch",branch)
            bb = repo.lookup_branch(branch)
            repo.checkout(bb)
            info("Switched to branch",branch)
            _git_push(path,remote,bb)
            # set branch upstream
            bb.upstream=repo.lookup_branch(remote+"/"+branch, self.GIT_BRANCH_REMOTE)

    def git_status(self,path,remote):
        repo = self.get_repo(path)
        st = repo.status()
        res = {
            "changes":{}
        }
        for k,v in st.items():
            res["changes"][k]=v
        # Get branches
        try:
            res["branch"]=repo.head.shorthand
            res["branches"]=[]
            for b in repo.listall_branches(self.GIT_BRANCH_LOCAL):
                bb = repo.lookup_branch(b)
                bu = bb.upstream.branch_name if bb.upstream else None
                res["branches"].append({"name":bb.branch_name,"upstream":bu})
        except Exception as e:
            print(e)
            res["branch"]=None
            res["branches"]=[]

        # get tags
        try:
            regex = re.compile('^refs/tags')
            tags = filter(lambda r: regex.match(r), repo.listall_references())
            tags = [t.replace('refs/tags/','') for t in tags]
            res["tags"]=tags
            res["tag"]=None
            for t in tags:
                tt = repo.lookup_reference('refs/tags/'+t)
                #print(tt.target,repo.get(tt.target),tt.get_object().id,repo.head.target)
                if tt.get_object().id==repo.head.target:
                    res["tag"]=t
                    break
        except Exception as e:
            print(e)
            res["tags"]=[]
            res["tag"]=None

        # get remote status
        r = self.get_remote(repo,remote)
        res["remote"]=remote

        try:
            try:
                remote_master_id = repo.lookup_reference('refs/remotes/'+remote+'/'+repo.head.shorthand).target
            except:
                warning("No branch",repo.head.shorthand,"in remote",remote)
                remote_master_id = repo.head.target
            
            ahead,behind = repo.ahead_behind(repo.head.target,remote_master_id)
            if ahead==behind and ahead==0:
                res["status"]="up to date"
            elif ahead>behind:
                res["status"]="newer"
            elif ahead<behind:
                res["status"]="older"
            else:
                res["status"]="unknown"
        except:
            res["status"]="uknown"

        return res

    def git_fetch(self,path,remote):
        repo = self.get_repo(path)
        r = self.get_remote(repo,remote)
        info("Fetching remote...")
        try:
            r.fetch()
        except Exception as e:
            fatal("Can't fetch",e)
        info("Ok")

    def git_commit(self,path,msg):
        repo = self.get_repo(path)
        index = repo.index
        st = repo.status()
        for k,v in st.items():
            if v>0:
                break
        else:
            warning("Nothing to commit")
            return
        info("Committing changes to local repository...")
        index.add_all()
        index.write()
        tree = index.write_tree()
        try:
            repo.head
            commit = repo.create_commit(repo.head.name, repo.default_signature, repo.default_signature, msg, tree, [repo.head.target])
        except:
            # first commit
            commit = repo.create_commit('refs/heads/master', repo.default_signature, repo.default_signature, msg, tree, [])
        info("Ok")


    def git_clone_external(self,url,dest,user=None,password=None):
        try:
            eurl = url
            if url.startswith("https://") or url.startswith("http://"):
                if user and password:
                    pos = url.find(":") #http(s):
                    eurl = url[:pos+3]+urllib.parse.quote(user)+":"+urllib.parse.quote(password)+"@"+url[pos+3:]
            repo = pygit2.clone_repository(eurl,dest)
        except Exception as e:
            fatal("Can't clone:",str(e))
        info("Ok")
        return eurl



    def git_clone(self,project,path):
        token = get_token()
        data = get_token_data()
        uid = data["uid"]
        url = env.git_url
        pos = url.find(":") #http(s):
        url = url[:pos+3]+token+":x-oauth-basic@"+url[pos+3:]+"/"+uid+"/"+project
        eurl = env.git_url+"/"+uid+"/"+project
        info("Cloning",eurl)
        try:
            repo = pygit2.clone_repository(url,path)
            repo.remotes.rename("origin","zerynth")
        except Exception as e:
            fatal("Can't clone:",str(e))
        info("Ok")
    
    def git_clone_from_url(self,url,user,password,path):
        orig_url = url
        pos = url.find(":") #http(s):
        if user and password:
            url = url[:pos+3]+user+":"+password+"@"+url[pos+3:]
        info("Cloning",orig_url)
        try:
            repo = pygit2.clone_repository(url,path)
        except Exception as e:
            fatal("Can't clone:",str(e))
        info("Ok")

    def git_init(self,path):
        pygit2.init_repository(path)

    def git_tag(self,path,tag):
        info("Tagging ",tag)
        repo = self.get_repo(path)
        try:
            oid = repo.create_tag(tag, repo.head.target, self.GIT_OBJ_COMMIT,repo.default_signature,"")
        except Exception as e:
            #if already existing
            warning("Tag",tag,e)
        return repo.lookup_reference("refs/tags/"+tag)

git = Git()
