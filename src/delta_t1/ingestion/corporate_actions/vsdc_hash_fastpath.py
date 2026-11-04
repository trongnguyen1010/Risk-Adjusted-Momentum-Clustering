"""Offline-only full-SHA256 fast path;no content/stat/digest caching or acquisition integration."""
from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat


@dataclass(frozen=True)
class Entry:
    name: str
    path: str
    expected_sha256: str


class FullHashPlan:
    """Compile approved names/expected hashes only;every check opens and hashes every entry again.

    Aliases/symlinks to regular files retain baseline semantics;equal expected hashes are
    deliberately not deduplicated. This is not an atomic filesystem snapshot,as with baseline.
    """
    def __init__(self,project,protected):
        root=Path(project).resolve();entries=[]
        for name,digest in protected.items():
            if not isinstance(name,str) or not isinstance(digest,str):raise ValueError('INVALID_PROTECTED_PLAN')
            path=PurePosixPath(name)
            if (not name or name=='.' or path.is_absolute() or PureWindowsPath(name).drive or '\\' in name or ':' in name
                    or '..' in path.parts or path.as_posix()!=name or not re.fullmatch('[0-9a-f]{64}',digest)):
                raise ValueError('INVALID_PROTECTED_PLAN: '+name)
            entries.append(Entry(name,str(root.joinpath(*path.parts)),digest))
        self._entries=tuple(entries)

    @property
    def entries(self):return self._entries

    def check(self):
        flags=os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NONBLOCK',0)
        for entry in self._entries:
            descriptor=None
            try:
                descriptor=os.open(entry.path,flags)
                with os.fdopen(descriptor,'rb') as stream:
                    descriptor=None  # Stream owns the handle,including all exception paths.
                    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                        raise ValueError('PROTECTED_OLD_FILE_CHANGED: '+entry.name)
                    if sha256(stream.read()).hexdigest()!=entry.expected_sha256:
                        raise ValueError('PROTECTED_OLD_FILE_CHANGED: '+entry.name)
            except OSError as exc:
                raise ValueError('PROTECTED_OLD_FILE_CHANGED: '+entry.name) from exc
            finally:
                if descriptor is not None:os.close(descriptor)


CONFIG='configs/data/corporate_actions/vsdc_hash_fastpath_offline_v1.json'
TYPE='vsdc-full-hash-fastpath-offline-benchmark-v1'


def contract():
    return {'stage':'VSDC_FULL_HASH_FASTPATH_OFFLINE_BENCHMARK_V1',
        'output':'data/corporate_actions/work/vsdc_hash_fastpath_offline_benchmark_20261103_v1',
        'warmup_per_implementation':2,'paired_rounds':8,'order':'ALTERNATING_AB_BA',
        'cohorts':{
            'active_V2_765':('data/corporate_actions/work/vsdc_remaining54_resumable_preparation_20261103_v2',
                '4d51178c54ffa1fd1952e91479403cf80eb53180584870884e3b4f0512773648',765),
            'profiled_shared864':('data/corporate_actions/work/vsdc_shared_browser2s_preparation_20261103_v1',
                '759263c4c487c2dcb36ee3198b074885c6ad23920e25b68eb753317288b30b39',864)},
        'review':'data/corporate_actions/work/vsdc_shared_browser2s_live_review_20261103_v1',
        'review_manifest_sha256':'9d21aaea9fcedfa36662e34b77dcf887ef29646ebcd1e2142b62ca62fdce9f5c',
        'full_read_every_file_every_check':True,'expected_hash_deduplication':False,
        'metadata_cache':False,'content_cache':False,'source_requests':0,'browser_launches':0,
        'runner_integration':False,'max_workers':1}


def benchmark(project):
    """Bounded local experiment on immutable real evidence;no source/browser operations."""
    from collections import Counter
    import platform
    from statistics import median
    import time
    from . import vsdc_shared_browser_pilot as pilot

    project=Path(project).resolve();config=pilot.read(project/CONFIG)
    # JSON serializes fixed cohort tuples as lists.
    import json
    if config!=json.loads(json.dumps(contract())):raise ValueError('EXACT_OFFLINE_HASH_BENCHMARK_REQUIRED')
    output=project/config['output']
    if output.exists():raise FileExistsError('REFUSE_OVERWRITE')
    pilot.load_preparation(project)
    review=project/config['review']
    if pilot.sha((review/'manifest.json').read_bytes())!=config['review_manifest_sha256']:
        raise ValueError('PINNED_HASH_PROFILING_EVIDENCE_CHANGED')
    pilot.verify_artifact(review,{'vsdc-shared-browser2s-offline-live-review-v1'})
    cohorts={};files={CONFIG:pilot.sha((project/CONFIG).read_bytes()),
        'src/delta_t1/ingestion/corporate_actions/vsdc_hash_fastpath.py':pilot.sha(Path(__file__).read_bytes()),
        'scripts/corporate_actions/benchmark_vsdc_hash_fastpath_v1.py':pilot.sha((project/'scripts/corporate_actions/benchmark_vsdc_hash_fastpath_v1.py').read_bytes())}
    for label,(rel,digest,count) in config['cohorts'].items():
        folder=project/rel
        if pilot.sha((folder/'manifest.json').read_bytes())!=digest:raise ValueError('COHORT_MANIFEST_CHANGED')
        pilot.verify_artifact(folder,{'vsdc-remaining54-user-pause-preparation-v2','vsdc-shared-browser2s-preparation-v1'})
        protected=pilot.read(folder/'protected_old_files.json')
        if len(protected)!=count:raise ValueError('COHORT_FILE_COUNT_CHANGED')
        cohorts[label]=(folder,protected)
    output.mkdir(parents=True);pilot.write(output/'config.json',config);pilot.write(output/'runtime.json',files)
    pilot.write(output/'environment.json',{'python':platform.python_version(),'OS':platform.system(),
        'OS_release':platform.release(),'clock':'perf_counter','workers':1,'warm_filesystem_cache':True,
        'limits':'Local disk/CPU timings;no source acquisition,OS cache flush or long-run walltime claims.'})
    outcomes={};profiles={}
    for label,(folder,protected) in cohorts.items():
        started=time.perf_counter();plan=FullHashPlan(project,protected);compile_seconds=time.perf_counter()-started
        # Baseline executes the unchanged function itself;candidate uses the same expected-map snapshot.
        calls={'baseline':lambda:pilot.mbs.old.protected_check(project,protected),'candidate':plan.check}
        for _ in range(config['warmup_per_implementation']):
            calls['baseline']();calls['candidate']()
        rounds=[]
        for number in range(config['paired_rounds']):
            order=['baseline','candidate'] if number%2==0 else ['candidate','baseline'];measurements={}
            for implementation in order:
                started=time.perf_counter();calls[implementation]();measurements[implementation]=time.perf_counter()-started
            rounds.append({'round':number+1,'order':order,'seconds':measurements})
        baseline_median=median(r['seconds']['baseline'] for r in rounds)
        candidate_median=median(r['seconds']['candidate'] for r in rounds)
        ratio=100*(baseline_median-candidate_median)/baseline_median
        profile={'metadata_path_seconds':0,'read_seconds':0,'SHA256_seconds':0,'files':len(protected),'bytes':0,
            'size_buckets':Counter(),'largest_files':[]}
        sizes=[]
        # One diagnostic pass with fine timers,separate from timing pairs;no data/hashes skipped.
        for name,digest in protected.items():
            started=time.perf_counter();path=project/name
            if not path.is_file():raise ValueError('PROTECTED_OLD_FILE_CHANGED: '+name)
            profile['metadata_path_seconds']+=time.perf_counter()-started
            started=time.perf_counter();data=(project/name).read_bytes();profile['read_seconds']+=time.perf_counter()-started
            started=time.perf_counter();actual=pilot.sha(data);profile['SHA256_seconds']+=time.perf_counter()-started
            if actual!=digest:raise ValueError('PROTECTED_OLD_FILE_CHANGED: '+name)
            size=len(data);profile['bytes']+=size;sizes.append((name,size))
            profile['size_buckets']['under16KB' if size<16384 else 'under1MB' if size<1048576 else 'over1MB']+=1
        profile['size_buckets']=dict(profile['size_buckets'])
        profile['largest_files']=[{'path':name,'bytes':size} for name,size in sorted(sizes,key=lambda row:row[1],reverse=True)[:7]]
        profiles[label]=profile
        outcomes[label]={'files':len(protected),'bytes_per_full_check':profile['bytes'],
            'expected_map_sha256':pilot.sha((folder/'protected_old_files.json').read_bytes()),
            'cohort_manifest_sha256':pilot.sha((folder/'manifest.json').read_bytes()),
            'compile_seconds':compile_seconds,'rounds':rounds,'baseline_median_seconds':baseline_median,
            'candidate_median_seconds':candidate_median,'median_reduction_percent':ratio,
            'candidate_faster_pairs':sum(r['seconds']['candidate']<r['seconds']['baseline'] for r in rounds),
            'all_full_reads_equivalent':True,'candidate_adoption':'OFFLINE_ONLY_NOT_INTEGRATED',
            'qualification':'PROMISING_LOCAL_FULL_HASH_MICROBENCHMARK' if ratio>=10 and sum(r['seconds']['candidate']<r['seconds']['baseline'] for r in rounds)>=7 else 'NO_CLEAR_LOCAL_GAIN'}
    pilot.load_preparation(project)
    pilot.write(output/'profiles.json',profiles);pilot.write(output/'paired_benchmarks.json',outcomes)
    status='PASS_OFFLINE_EQUIVALENCE_AND_LOCAL_SPEEDUP' if all(r['qualification']=='PROMISING_LOCAL_FULL_HASH_MICROBENCHMARK' for r in outcomes.values()) else 'PASS_OFFLINE_EQUIVALENCE_NO_CONSISTENT_SPEEDUP'
    result={'status':status,'cohorts':outcomes,'source_requests':0,'browser_launches':0,'runner_changed':False,
        'full_read_every_file_every_check':True,'files_deduplicated':0,'metadata_or_content_cache':False,
        'existing_source_request_cadence_unchanged':True,
        'limits':['Warm-cache single-machine paired8-round microbenchmark;not a source/live-crawl or end-to-end speed guarantee.',
            'Compiler cost excluded from steady checks and recorded separately;plan stores expected names/digests only.',
            'Neither old nor new verifier is an atomic snapshot against adversarial concurrent filesystem replacement.',
            'Shorter local hashing can increase remaining2s pacing wait;do not extrapolate these percentages to total collection.',
            'No integration into immutable V1/V2 or source pilots in this stage.']}
    pilot.write(output/'result.json',result)
    pilot.write(output/'manifest.json',{'artifact_type':TYPE,'files':pilot.hashes(output)})
    pilot.verify_artifact(output,{TYPE})
    return {'status':status,'output':str(output),'cohorts':{k:{name:v[name] for name in ('files','baseline_median_seconds','candidate_median_seconds','median_reduction_percent','candidate_faster_pairs')} for k,v in outcomes.items()},'source_requests':0,'browser_launches':0,'runner_changed':False}
