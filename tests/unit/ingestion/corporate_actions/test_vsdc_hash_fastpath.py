from hashlib import sha256
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from delta_t1.ingestion.corporate_actions import vsdc_hash_fastpath as p
from delta_t1.ingestion.corporate_actions.vsdc_mbs_browser_html import protected_check


class FullHashTests(unittest.TestCase):
    def inventory(self,tmp):
        root=Path(tmp);data={'nested/tiếng Việt α.bin':b'\x00\xffbinary\n'*30,
            'empty.json':b'','same1.json':b'same content','same2.json':b'same content',
            'large.bin':bytes(range(256))*8192}
        for name,body in data.items():
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(body)
        return root,{name:sha256(body).hexdigest() for name,body in data.items()}

    def verify_both_fail(self,root,protected,plan):
        for verifier in (lambda:protected_check(root,protected),plan.check):
            with self.assertRaises(ValueError):verifier()

    def test_identical_stable_empty_binary_unicode_nested_large_files_and_repeated_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,protected=self.inventory(tmp);plan=p.FullHashPlan(root,protected)
            for _ in range(3):self.assertIsNone(protected_check(root,protected));self.assertIsNone(plan.check())
            self.assertEqual(list(protected),[entry.name for entry in plan.entries])
            self.assertIsInstance(plan.entries,tuple)

    def test_same_size_content_edit_with_original_mtime_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,protected=self.inventory(tmp);plan=p.FullHashPlan(root,protected);plan.check()
            path=root/'same1.json';before=path.stat();path.write_bytes(b'evil content')
            self.assertEqual(before.st_size,path.stat().st_size)
            os.utime(path,ns=(before.st_atime_ns,before.st_mtime_ns))
            self.assertEqual(before.st_mtime_ns,path.stat().st_mtime_ns)
            self.verify_both_fail(root,protected,plan)

    def test_last_byte_large_file_edit_cannot_escape_full_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,protected=self.inventory(tmp);plan=p.FullHashPlan(root,protected)
            with (root/'large.bin').open('r+b') as stream:stream.seek(-1,2);stream.write(b'\x00')
            self.verify_both_fail(root,protected,plan)

    def test_deleted_truncated_appended_and_directory_replacement_fail_equivalently(self):
        for mode in ('deleted','truncated','appended','directory'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root,protected=self.inventory(tmp);plan=p.FullHashPlan(root,protected);path=root/'same1.json'
                if mode=='deleted':path.unlink()
                elif mode=='truncated':path.write_bytes(b'same')
                elif mode=='appended':
                    with path.open('ab') as stream:stream.write(b'extra')
                else:path.unlink();path.mkdir()
                self.verify_both_fail(root,protected,plan)

    def test_atomic_file_replacement_same_size_and_timestamp_is_not_cached(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,protected=self.inventory(tmp);plan=p.FullHashPlan(root,protected);plan.check()
            original=root/'same1.json';before=original.stat();replacement=root/'replacement'
            replacement.write_bytes(b'evil content');os.utime(replacement,ns=(before.st_atime_ns,before.st_mtime_ns))
            os.replace(replacement,original)
            self.verify_both_fail(root,protected,plan)

    def test_equal_expected_hashes_are_not_deduplicated_and_each_call_reopens_all_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,protected=self.inventory(tmp);plan=p.FullHashPlan(root,protected)
            original_open=p.os.open
            with patch.object(p.os,'open',wraps=original_open) as opened:
                plan.check();plan.check();self.assertEqual(2*len(protected),opened.call_count)
            # Alter only the second duplicate;reusing first file's hash would incorrectly pass.
            (root/'same2.json').write_bytes(b'evil content')
            self.verify_both_fail(root,protected,plan)

    def test_each_call_reads_bytes_again_no_content_or_stat_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,protected=self.inventory(tmp);plan=p.FullHashPlan(root,protected)
            original=p.sha256
            with patch.object(p,'sha256',wraps=original) as hashed:
                plan.check();plan.check()
                self.assertEqual(2*len(protected),hashed.call_count)
                first=[call.args[0] for call in hashed.call_args_list[:len(protected)]]
                second=[call.args[0] for call in hashed.call_args_list[len(protected):]]
                self.assertEqual(first,second)
                self.assertEqual(sum((root/name).stat().st_size for name in protected),sum(map(len,first)))

    def test_unreadable_file_and_nonregular_descriptor_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,protected=self.inventory(tmp);plan=p.FullHashPlan(root,protected)
            with patch.object(p.os,'open',side_effect=PermissionError('DENIED')):
                with self.assertRaisesRegex(ValueError,'PROTECTED_OLD_FILE_CHANGED'):plan.check()
            with patch.object(p.stat,'S_ISREG',return_value=False):
                with self.assertRaisesRegex(ValueError,'PROTECTED_OLD_FILE_CHANGED'):plan.check()

    def test_open_descriptor_closed_if_stream_construction_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,protected=self.inventory(tmp);plan=p.FullHashPlan(root,protected)
            real_close=p.os.close
            with patch.object(p.os,'fdopen',side_effect=OSError('STREAM_FAILED')),patch.object(p.os,'close',wraps=real_close) as closed:
                with self.assertRaises(ValueError):plan.check()
                closed.assert_called_once()
            # No leaked handle preventing subsequent file access on Windows.
            plan.check()

    def test_frozen_expected_map_snapshot_does_not_accept_later_manifest_dictionary_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,protected=self.inventory(tmp);plan=p.FullHashPlan(root,protected)
            path=root/'same1.json';path.write_bytes(b'evil content');protected['same1.json']=sha256(path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError,'same1.json'):plan.check()

    def test_invalid_plan_paths_or_hashes_are_rejected_without_opening_files(self):
        for name,digest in [('../outside','a'*64),('/absolute','a'*64),('C:/outside','a'*64),('C:outside','a'*64),
                ('a\\b','a'*64),('folder/file:stream','a'*64),('a//b','a'*64),('.','a'*64),('','a'*64),
                ('file','no digest'),('file','A'*64),('file',None),(None,'a'*64)]:
            with self.subTest(name=name),patch.object(p.os,'open') as opened,self.assertRaises(ValueError):p.FullHashPlan('.',{name:digest})
            opened.assert_not_called()

    def test_empty_protected_set_matches_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(protected_check(Path(tmp),{}));self.assertIsNone(p.FullHashPlan(tmp,{}).check())


if __name__=='__main__':unittest.main()
