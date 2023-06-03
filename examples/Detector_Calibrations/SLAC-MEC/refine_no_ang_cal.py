import MILK
import sys

if __name__ == '__main__':

    config = MILK.load_json('milk.json')
    editor = MILK.parameterEditor.editor()
    editor.parseConfig(config, ifile=sys.argv[1],ofile=sys.argv[1])
    maudText = MILK.maud.maudText()
    maudText.parseConfig(config)

    #Add slope term to angle correction
    editor.add_loop_par(key='_riet_par_2-theta_offset')

    #Free calibration parameters and background, no intensity scaling since template already has arbitrary texture 
    editor.fix_all()
    editor.free(key='Background')
    maudText.refinement(itr='4', ifile=editor.ifile,ofile=editor.ofile,simple_call=True)

    #Refine peak shape (first make sure no broadening model is turned on)
    editor.set_val(key='MicroStrain',value='0.0')
    editor.set_val(key='CrystSize',value='0.0')
    editor.set_val(key='_riet_par_asymmetry_value',value='0.0')
    editor.set_val(key='_riet_par_gaussian_value',value='0.0')
    editor.set_val(key='_riet_par_caglioti_value',value='0.0')
    editor.set_val(key='_riet_par_caglioti_value',value='0.00001',loopid='0')
    editor.free(key='_riet_par_caglioti_value',loopid='0')
    editor.free(key='_riet_par_2-theta_offset')
    maudText.refinement(itr='4', ifile=editor.ifile,ofile=editor.ofile,simple_call=True)

    editor.fix(key='_riet_par_caglioti_value',loopid='0')
    editor.free(key='_riet_par_caglioti_value',loopid='1')
    maudText.refinement(itr='4', ifile=editor.ifile,ofile=editor.ofile,simple_call=True)

    editor.fix(key='_riet_par_caglioti_value',loopid='1')
    editor.free(key='_riet_par_caglioti_value',loopid='2')
    maudText.refinement(itr='4', ifile=editor.ifile,ofile=editor.ofile,simple_call=True)

    editor.fix(key='_riet_par_caglioti_value',loopid='2')
    editor.free(key='_riet_par_gaussian_value',loopid='0')
    maudText.refinement(itr='4', ifile=editor.ifile,ofile=editor.ofile,simple_call=True)

    editor.fix(key='_riet_par_gaussian_value',loopid='0')
    editor.free(key='_riet_par_caglioti_value',loopid='1')
    editor.free(key='_riet_par_caglioti_value',loopid='2')
    maudText.refinement(itr='4', ifile=editor.ifile,ofile=editor.ofile,simple_call=True)