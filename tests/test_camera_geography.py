from film_lab.production import Take
from film_lab.camera_geography import evaluate_camera_geography

def _take(tid,camera,*,start=(0,0),end=(1,0),allow=False):
    return Take(tid,'scene','shot','/tmp/x.mp4',metadata={'camera_geography_intent':{'line_of_action_start':list(start),'line_of_action_end':list(end),'camera_position':list(camera),'allow_axis_cross':allow}})

def test_same_side_of_action_axis_passes():
    r=evaluate_camera_geography(_take('a',(.2,1)),_take('b',(.8,1)))
    assert r.status=='PASS' and r.side_status=='PASS' and r.from_side==r.to_side=='LEFT'

def test_unmotivated_axis_cross_is_high_review():
    r=evaluate_camera_geography(_take('a',(.2,1)),_take('b',(.8,-1)))
    assert r.side_status=='REVIEW'
    assert any(x['domain']=='180_degree_rule' and x['severity']=='HIGH' for x in r.issues)

def test_explicit_axis_cross_still_requires_director_review_not_failure():
    r=evaluate_camera_geography(_take('a',(.2,1)),_take('b',(.8,-1),allow=True))
    assert r.status=='REVIEW'
    assert r.evidence['axis_cross_explicitly_allowed'] is True
    assert not any(x['severity']=='HIGH' for x in r.issues)

def test_missing_explicit_geography_is_not_guessed():
    a=Take('a','scene','s1','/tmp/a.mp4'); b=Take('b','scene','s2','/tmp/b.mp4')
    r=evaluate_camera_geography(a,b)
    assert r.status=='NOT_TESTED' and r.side_status=='NOT_TESTED' and r.axis_status=='NOT_TESTED'
