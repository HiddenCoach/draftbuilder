import sys,unittest
sys.path.insert(0,'/mnt/data/lol_draft_lab')
from draft_intelligence import recommend_bans,recommend_picks,open_roles
class TestDraft(unittest.TestCase):
 def setUp(self):
  self.plan={'TOP':'K’Sante','JGL':'Jarvan IV','MID':'Orianna','ADC':'Jhin','SUP':'Nautilus'}
 def test_bans_exclude_own_and_used(self):
  result=recommend_bans(self.plan,{'JGL':'Jarvan IV'},[],['Poppy','Renata Glasc'],['Poppy','Renata Glasc','Olaf'])
  names=[x['name'] for x in result]
  self.assertNotIn('Poppy',names);self.assertNotIn('Renata Glasc',names)
  self.assertFalse(set(names)&set(self.plan.values()))
 def test_bans_recalculate_after_pick(self):
  a=recommend_bans(self.plan,{},[],[],[])
  b=recommend_bans(self.plan,{'ADC':'Xayah'},[],[],[])
  self.assertNotEqual([(x['name'],x['score']) for x in a],[(x['name'],x['score']) for x in b])
 def test_no_second_role(self):
  result=recommend_picks(self.plan,{'JGL':'Jarvan IV','MID':'Orianna'},['Jarvan IV','Orianna'])
  self.assertFalse(any(x['role'] in ('JGL','MID') for x in result))
 def test_enemy_role_locked(self):
  result=recommend_bans(self.plan,{},[],[],[],{'ADC':'Ezreal','SUP':'Braum'})
  self.assertNotIn('Xayah',[x['name'] for x in result])
if __name__=='__main__':unittest.main()
